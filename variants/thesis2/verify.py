from pathlib import Path
import json,re,hashlib,collections,sys,subprocess,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[2];v=r/'variants/thesis2';q=r/'build/thesis2/verification';q.mkdir(parents=True,exist_ok=True);b=json.loads((v/'audit/baseline.json').read_text());m=json.loads((v/'audit/edits.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda s:re.sub(r'\s+',' ',s).strip()
# Read earlier editorial stages from their exact before-images. The final layer
# is checked independently against current files below; historical records stay fixed.
final_path=v/'audit/final-review-2026-10-30.json'
final_record=json.loads(final_path.read_text()) if final_path.exists() else {}
final_changes={x['path']:x for x in final_record.get('changes',[])}
def historical_text(path):
 rel=str(path.relative_to(r))
 return final_changes[rel]['before'] if rel in final_changes else path.read_text()
def historical_sha(path):
 return hashlib.sha256(historical_text(path).encode()).hexdigest() if str(path.relative_to(r)) in final_changes else sha(path)
document_record_path=v/'audit/ch7-review-2026-10-30.json'
document_record=json.loads(document_record_path.read_text()) if document_record_path.exists() else {}
authorised_document_updates={x['path']:x for x in document_record.get('document_changes',[])}
assert set(authorised_document_updates)<={'assessment/ch7-pending-experiments.txt'},'Protected-document update scope'
missing=[]
for rel,h in b['protected_files'].items():
 if not (r/rel).exists():
  assert rel in ['thesis1-part1.pdf','thesis1-part2.pdf'],('Protected file missing',rel)
  missing.append(rel)
 elif rel in authorised_document_updates:
  change=authorised_document_updates[rel]
  assert hashlib.sha256(change['before'].encode()).hexdigest()==h,('Protected document before-image',rel)
  assert (r/rel).read_text()==change['after'],('Protected document after-image',rel)
 else:assert sha(r/rel)==h,('Protected file changed',rel)
# Exact replay from thesis1-routed source, including every unedited source gap.
expected=dict(b['variant_source_before'])
for rel in {x['path'] for x in m['blocks']}:
 vr=str(Path(rel).relative_to('variants/thesis2'));old=expected[vr];s=old
 for x in sorted([x for x in m['blocks'] if x['path']==rel],key=lambda x:x['start'],reverse=True):
  assert old[x['start']:x['end']]==x['before'],x['id'];s=s[:x['start']]+x['after']+s[x['end']:]
  for sent in x['sentences']:
   if sent['blue']<=.05 and sent['match']>=.9 and len(sent['text'].split())>=8:assert norm(sent['text']) in norm(x['after']),(x['id'],'unmarked sentence')
  for env in ['lemma','proposition','corollary']:
   pat=r'\\begin\{'+env+r'\}[\s\S]*?\\end\{'+env+r'\}';assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(x['id'],env)
  assert not any(ord(c)<32 and c not in '\t\n' for c in x['after']),x['id']
 expected[vr]=s
for x in m['structural']:
 vr=str(Path(x['path']).relative_to('variants/thesis2'));assert expected[vr]==x['before'],('structural before-image',vr);expected[vr]=x['after']
# Preserve the historical ledger; replay this round only from its exact before-images.
round_path=v/'audit/figure-layout-2026-10-30.json';round_record=json.loads(round_path.read_text())
assert sha(v/'audit/edits.json')==round_record['historical_ledger_sha256'],'Historical ledger modified'
for rel,s in round_record['baseline_additional_tex'].items():
 assert rel not in expected,('Already tracked historical source',rel)
 expected[rel]=s
for x in round_record['changes']:
 vr=str(Path(x['path']).relative_to('variants/thesis2'))
 assert expected.get(vr)==x['before'],('New-round before-image',vr)
 expected[vr]=x['after']
# Author-confirmed ownership is a separate, traceable follow-up to the figure round.
personal=json.loads((v/'audit/individual-contribution-2026-10-30.json').read_text())
for rel,h in personal['historical_ledger_hashes'].items():assert sha(r/rel)==h,('Historical audit changed',rel)
for x in personal['changes']:
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'));assert expected[vr]==x['before'],('Ownership before-image',vr)
 owned=x['before'].rstrip()+'\n\n'+x['addition']
 if x.get('kind')=='addition_and_layout':
  wrap=x['layout_wrapper'];assert owned.count(wrap['marker'])==1,vr
  owned=owned.replace(wrap['marker'],wrap['prefix']+wrap['marker'],1)+wrap['suffix']
 assert x['after']==owned,vr
 for env in ['lemma','proposition','corollary','proof']:
  pat=r'\\begin\{'+env+r'\}[\s\S]*?\\end\{'+env+r'\}';assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
 assert re.findall(r'\\toprule([\s\S]*?)\\bottomrule',x['before'])==re.findall(r'\\toprule([\s\S]*?)\\bottomrule',x['after']),vr
 expected[vr]=x['after']
# Targeted response to the subsequent review; preserve the earlier audit layers.
review_path=v/'audit/review-02a4467-2026-10-30.json'
review=json.loads(review_path.read_text())
for rel,h in review['historical_hashes'].items():assert sha(r/rel)==h,('Historical review input changed',rel)
for x in review['changes']:
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'));assert expected[vr]==x['before'],('Review before-image',vr)
 for env in ['lemma','proposition','corollary','proof','equation','equation*','align','align*']:
  pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
 assert re.findall(r'\\toprule([\s\S]*?)\\bottomrule',x['before'])==re.findall(r'\\toprule([\s\S]*?)\\bottomrule',x['after']),vr
 assert re.findall(r'\\\[[\s\S]*?\\\]',x['before'])==re.findall(r'\\\[[\s\S]*?\\\]',x['after']),vr
 expected[vr]=x['after']
for rel,content in review['added_files'].items():assert (r/rel).read_text()==content,('New reference file',rel)
front_record=json.loads((v/'audit/frontmatter-review-2026-10-30.json').read_text())
mention_path=v/'audit/first-mention-review-2026-10-30.json'
mention_record=json.loads(mention_path.read_text()) if mention_path.exists() else {}
mention_changes={x['path']:x for x in mention_record.get('changes',[])}
technical_figure_path=mention_record.get('technical_figure_followup',{}).get('record')
technical_figures=json.loads((r/technical_figure_path).read_text()) if technical_figure_path else {}
technical_changes={x['path']:x for x in technical_figures.get('changes',[])}
ch3_followup_path=mention_record.get('chapter3_readability_followup',{}).get('record')
ch3_followup=json.loads((r/ch3_followup_path).read_text()) if ch3_followup_path else {}
ch3_followup_changes={x['path']:x for x in ch3_followup.get('changes',[])}
ch56_path=mention_record.get('chapter56_structure_followup',{}).get('record')
ch56_review=json.loads((r/ch56_path).read_text()) if ch56_path else {}
ch56_changes={x['path']:x for x in ch56_review.get('changes',[])}
cpu_conclusion_path=mention_record.get('cpu_conclusion_followup',{}).get('record')
cpu_conclusion=json.loads((r/cpu_conclusion_path).read_text()) if cpu_conclusion_path else {}
cpu_conclusion_changes={x['path']:x for x in cpu_conclusion.get('changes',[])}
ch8_path=mention_record.get('chapter8_structure_followup',{}).get('record')
ch8_review=json.loads((r/ch8_path).read_text()) if ch8_path else {}
ch8_changes={x['path']:x for x in ch8_review.get('changes',[])}
ch7_path=mention_record.get('chapter7_structure_followup',{}).get('record')
ch7_review=json.loads((r/ch7_path).read_text()) if ch7_path else {}
ch7_changes={x['path']:x for x in ch7_review.get('changes',[])}
terminology=mention_record.get('terminology_followup',{})
term_changes={x['path']:x for x in terminology.get('changes',[])}
concise_review=mention_record.get('concise_prose_followup',{})
concise_changes={x['path']:x for x in concise_review.get('changes',[])}
chapter4_review=mention_record.get('chapter4_structure_followup',{})
chapter4_changes={x['path']:x for x in chapter4_review.get('changes',[])}
rq_followup=mention_record.get('rq_alignment_followup',{})
rq_changes={x['path']:x for x in rq_followup.get('changes',[])}
if rq_changes:
 assert set(rq_changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in ['01-4-questions.tex','03-1-comparisons.tex','09-conclusion.tex']},'RQ alignment scope'
background=mention_record.get('background_review',{})
background_paths=set(background.get('paths',[]))
protocol=mention_record.get('protocol_review',{})
protocol_paths=set(protocol.get('paths',[]))
if protocol_paths:
 assert protocol_paths=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in ['03-methodology.tex','03-1-comparisons.tex','03-2-data.tex','03-3-measurement.tex','03-4-frontiers.tex','03-5-ledger.tex','04-2-training.tex','04-6-contracts.tex']},'Protocol review scope'
 for rel,h in protocol['frozen_chapters'].items():
  prior=rq_changes.get(rel,term_changes.get(rel,{})).get('before')
  observed=hashlib.sha256(prior.encode()).hexdigest() if prior is not None else historical_sha(r/rel)
  assert observed==h,('Chapter 1/2 changed during protocol review',rel)
 for lang in ['thesis2','thesis2-zh']:
  edits=[mention_changes[p] for p in sorted(protocol_paths) if p.startswith('variants/'+lang+'/')]
  old='\n'.join(x['before'] for x in edits);new='\n'.join(x['after'] for x in edits)
  for x in edits:
   for env in ['equation','align','equation*','align*','lemma','proposition','corollary','proof']:
    pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
    assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(x['path'],env)
   assert re.findall(r'\\\[[\s\S]*?\\\]',x['before'])==re.findall(r'\\\[[\s\S]*?\\\]',x['after']),(x['path'],'Protocol display mathematics')
  labels=collections.Counter(re.findall(r'\\label\{[^}]+\}',old));labels.subtract([r'\label{sec:3-6}'])
  assert +labels==collections.Counter(re.findall(r'\\label\{[^}]+\}',new)),('Protocol labels',lang)
  pat=r'\\cite(?:\[[^]]*\])?\{[^}]+\}'
  assert collections.Counter(re.findall(pat,old))==collections.Counter(re.findall(pat,new)),('Protocol citations',lang)
  refs=collections.Counter(re.findall(r'\\[Cc]ref\{[^}]+\}',old));refs.subtract(protocol['removed_reference_commands']);refs.update(protocol['added_reference_commands'])
  assert +refs==collections.Counter(re.findall(r'\\[Cc]ref\{[^}]+\}',new)),('Protocol references',lang)
if background_paths:
 assert background_paths=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in ['02-background.tex','02-1-objective.tex','02-2-hierarchy.tex','02-3-jhq.tex','02-4-gpu.tex','02-5-graphs.tex','02-6-quantised.tex','02-7-gap.tex']},'Chapter-2 scope'
 sign_source=term_changes.get('variants/thesis2/chapters/04-2-training.tex',{}).get('before',historical_text(v/'chapters/04-2-training.tex'))
 if 'variants/thesis2/chapters/04-2-training.tex' in protocol_paths:sign_source=re.sub(r'\bK0\b','C0',sign_source)
 assert hashlib.sha256(sign_source.encode()).hexdigest()==background['unchanged_later_sign_derivation_sha256'],'Retained sign derivation changed'
 for lang in ['thesis2','thesis2-zh']:
  edits=[mention_changes[p] for p in sorted(background_paths) if p.startswith('variants/'+lang+'/')]
  old='\n'.join(x['before'] for x in edits);new='\n'.join(x['after'] for x in edits)
  for env in ['lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+env+r'\}[\s\S]*?\\end\{'+env+r'\}'
   assert re.findall(pat,old)==re.findall(pat,new),('Chapter-2 formal proof',lang,env)
  def equations(s):
   return {re.search(r'\\label\{([^}]+)\}',block)[1]:block for block in re.findall(r'\\begin\{equation\}[\s\S]*?\\end\{equation\}',s)}
  eq_old,eq_new=equations(old),equations(new)
  assert set(eq_old)-set(eq_new)=={'eq:2-sign-order'} and not set(eq_new)-set(eq_old),('Duplicate equation scope',lang)
  assert {k:val for k,val in eq_old.items() if k!='eq:2-sign-order'}==eq_new,('Core background equations changed',lang)
  old_labels=collections.Counter(re.findall(r'\\label\{[^}]+\}',old));old_labels.subtract([r'\label{eq:2-sign-order}'])
  assert +old_labels==collections.Counter(re.findall(r'\\label\{[^}]+\}',new)),('Background labels',lang)
  pat=r'\\cite(?:\[[^]]*\])?\{[^}]+\}'
  assert collections.Counter(re.findall(pat,old))==collections.Counter(re.findall(pat,new)),('Background citations',lang)
  old_refs=collections.Counter(re.findall(r'\\[Cc]ref\{[^}]+\}',old));old_refs.update(background['added_cross_references'])
  assert old_refs==collections.Counter(re.findall(r'\\[Cc]ref\{[^}]+\}',new)),('Background cross-references',lang)
  displays_old=re.findall(r'\\\[[\s\S]*?\\\]',old);displays_new=re.findall(r'\\\[[\s\S]*?\\\]',new)
  retained=[block for block in displays_old if any(key in block for key in ['U(q)=','r_{\\rm IVF','|\\mathcal R_\\alpha','W_{\\rm primary}','a_{\\rm MSE}'])]
  primary='\\[\n \\primarydist=\\|q\'-\\widehat p\\|^2.\n\\]'
  assert len(retained)==5 and collections.Counter(displays_new)==collections.Counter(retained+[primary]),('Background display moves/deduplication',lang)
def validate_intro_table(before,after,edit,rel):
 assert rel=='chapters/01-5-contributions.tex' and before==edit['before'] and after==edit['after'],('Unapproved table rewrite',rel)
 def numbers(s):
  return [[collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',c)) for c in row.split('&')] for row in s.split('\\midrule',1)[1].split('\\\\') if row.strip()]
 a,b=numbers(before),numbers(after);assert len(a)==len(b)==3
 for i,(ra,rb) in enumerate(zip(a,b)):
  assert len(ra)==len(rb)==4
  for j,(ca,cb) in enumerate(zip(ra,rb)):
   target=ca+collections.Counter({'0.0006':1}) if (i,j)==(2,3) else ca
   assert target==cb,(rel,i,j,ca,cb)
 losses=[float(line.split('&')[3]) for line in (r/'tables/ch7/budget_full.tex').read_text().splitlines() if re.match(r'^(Vogue|arXiv|OpenAI|BGE|Stella)',line)]
 assert len(losses)==12 and max(losses)==0.0006,'Introductory calibration loss must match existing measurements'
for rel,h in mention_record.get('frozen_records',{}).items():assert sha(r/rel)==h,('Prior readability input changed',rel)
for rel,h in mention_record.get('unchanged_source_hashes',{}).items():
 prior=term_changes.get(rel,concise_changes.get(rel,chapter4_changes.get(rel,technical_changes.get(rel,ch3_followup_changes.get(rel,ch56_changes.get(rel,cpu_conclusion_changes.get(rel,ch8_changes.get(rel,ch7_changes.get(rel,{}))))))))).get('before')
 observed=hashlib.sha256(prior.encode()).hexdigest() if prior is not None else historical_sha(r/rel)
 assert observed==h,('Unrecorded readability source change',rel)
for group in ['chapter_sources_unchanged','shared_frontmatter_unchanged','historical_ledgers_unchanged','frozen_style_previews']:
 for rel,h in front_record[group].items():
  before=mention_changes.get(rel,term_changes.get(rel,concise_changes.get(rel,chapter4_changes.get(rel,technical_changes.get(rel,ch3_followup_changes.get(rel,ch56_changes.get(rel,cpu_conclusion_changes.get(rel,ch8_changes.get(rel,ch7_changes.get(rel,{})))))))))).get('before')
  observed=hashlib.sha256(before.encode()).hexdigest() if before is not None else historical_sha(r/rel)
  assert observed==h,('Frontmatter scope changed before readability follow-up',rel)
for x in front_record['changes']:
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'))
 assert expected.get(vr)==x['before'],('Frontmatter before-image',vr)
 expected[vr]=x['after']
for x in mention_record.get('changes',[]):
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'))
 assert expected[vr]==x['before'],('First-mention before-image',vr)
 if x['path'] in background_paths or x['path'] in protocol_paths:
  expected[vr]=x['after'];continue
 for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
  pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
 display_before=x['before']
 for edit in x.get('authorised_display_edits',[]):
  assert vr in ['chapters/01-1-context.tex','chapters/01-2-scope.tex','chapters/01-3-challenges.tex'] and display_before.count(edit['before'])==1,('Unapproved introductory display edit',vr)
  if vr=='chapters/01-1-context.tex':assert edit['after']==edit['before'].replace(r'=\frac{32607}{1024}',r'\simeq31.8')
  else:assert edit['after']=='',('Only introductory display removal approved',vr)
  display_before=display_before.replace(edit['before'],edit['after'],1)
 pat=r'\\\[[\s\S]*?\\\]';assert re.findall(pat,display_before)==re.findall(pat,x['after']),(vr,pat)
 pat=r'\\toprule([\s\S]*?)\\bottomrule';old_tables,new_tables=re.findall(pat,x['before']),re.findall(pat,x['after'])
 if x.get('authorised_table_rewording'):
  assert len(old_tables)==len(new_tables)==1
  validate_intro_table(old_tables[0],new_tables[0],x['authorised_table_rewording'],vr)
 else:assert old_tables==new_tables,(vr,pat)
 for cmd in ['label','cite','Cref','cref']:
  pat=r'\\'+cmd+r'(?:\[[^]]*\])?\{[^}]*\}'
  before_refs=collections.Counter(re.findall(pat,x['before']))
  for added in x.get('added_reference_commands',[]):
   assert added==r'\cref{tab:1-contributions}' and vr=='chapters/01-5-contributions.tex',('Unapproved reference addition',vr,added)
   if re.fullmatch(pat,added):before_refs.update([added])
  for removed in x.get('removed_reference_commands',[]):
   assert removed in [r'\Cref{fig:1-challenges}',r'\label{fig:1-challenges}'] and vr=='chapters/01-3-challenges.tex',('Unapproved reference removal',vr,removed)
   if re.fullmatch(pat,removed):
    assert before_refs[removed]==1,(vr,removed)
    before_refs.subtract([removed])
  assert +before_refs==collections.Counter(re.findall(pat,x['after'])),(vr,cmd)
 expected[vr]=x['after']
for x in rq_followup.get('changes',[]):
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'));assert expected[vr]==x['before'],('RQ follow-up before-image',vr)
 for env in ['equation','align','equation*','align*','lemma','proposition','corollary','proof']:
  pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
 for pat in [r'\\\[[\s\S]*?\\\]',r'\\(?:label|cite|Cref|cref)\{[^}]+\}']:
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,pat)
 assert re.findall(r'\d+(?:[,.]\d+)*',x['before'])==re.findall(r'\d+(?:[,.]\d+)*',x['after']),(vr,'RQ follow-up numbers')
 expected[vr]=x['after']
for x in terminology.get('changes',[]):
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'))
 assert expected[vr]==x['before'],('Terminology before-image',vr)
 for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
  pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Terminology formal block',env)
 for pat in [r'\\\[[\s\S]*?\\\]',r'\\toprule[\s\S]*?\\bottomrule',r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}']:
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Terminology scope',pat)
 assert collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',x['before']))==collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',x['after'])),(vr,'Terminology numerical values')
 expected[vr]=x['after']
timing_review=mention_record.get('timing_boundary_followup',{})
if timing_review:
 assert sha(r/'figures/ch3/measurement-boundary.tex')==timing_review['shared_figure_sha256'],'Shared measurement diagram changed'
 assert {x['path'] for x in timing_review['changes']}=={'variants/'+lang+'/chapters/03-3-measurement.tex' for lang in ['thesis2','thesis2-zh']},'Timing follow-up scope'
 for x in timing_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Timing follow-up before-image',vr)
  for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
   assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
  for pat in [r'\\\[[\s\S]*?\\\]',r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}']:
   assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,pat)
  def timing_numbers(s):
   s=re.sub(r'\\resizebox\{\\linewidth\}\{!\}[\s\S]*?\\label\{fig:3-boundary\}','',s)
   return collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',s))
  assert timing_numbers(x['before'])==timing_numbers(x['after']),'Timing measurements changed'
  expected[vr]=x['after']
 assert set(timing_review['added_files'])=={'variants/thesis2/figures/measurement-boundary.tex'},'Timing diagram scope'
 for rel,source in timing_review['added_files'].items():
  vr=str(Path(rel).relative_to('variants/thesis2'))
  assert vr not in expected and (r/rel).read_text()==source,('Timing diagram source',rel)
  expected[vr]=source
for x in concise_review.get('changes',[]):
 if not x['path'].startswith('variants/thesis2/'):continue
 vr=str(Path(x['path']).relative_to('variants/thesis2'))
 assert expected[vr]==x['before'],('Concise prose before-image',vr)
 for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
  pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
 for pat in [r'\\\[[\s\S]*?\\\]',r'\\toprule[\s\S]*?\\bottomrule',r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}']:
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,pat)
 def concise_numbers(s):
  if vr=='chapters/07-supp-precision.tex':s=re.sub(r'\b(?:E1|TF32)\b','',s)
  return collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',s))
 assert concise_numbers(x['before'])==concise_numbers(x['after']),(vr,'Measured values changed')
 expected[vr]=x['after']
structure_review=mention_record.get('chapter3_structure_followup',{})
if structure_review:
 changes=structure_review['changes']
 paths={'variants/'+lang+'/chapters/03-'+str(n)+'-'+tail+'.tex' for lang in ['thesis2','thesis2-zh'] for n,tail in [(1,'comparisons'),(2,'data'),(3,'measurement'),(4,'frontiers'),(5,'ledger')]}
 assert {x['path'] for x in changes}==paths,'Chapter 3 structure scope'
 removals={x['path']:x for x in structure_review['authorised_removals']}
 for x in changes:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Chapter 3 structure before-image',vr)
  for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
   assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
  pat=r'\\\[[\s\S]*?\\\]';old_displays=re.findall(pat,x['before'])
  if vr=='chapters/03-3-measurement.tex':
   allowed=removals[x['path']]['blocks']
   assert len(allowed)==2 and old_displays==allowed and not re.findall(pat,x['after']),'Only two unlabelled timing illustrations may be removed'
   pat_fig=r'\\par\\medskip\\noindent\\begin\{minipage\}[\s\S]*?\\end\{minipage\}\\par\\medskip'
   assert re.search(pat_fig,x['before'])[0]==re.search(pat_fig,x['after'])[0],'Figure 3.1 block changed'
  else:assert old_displays==re.findall(pat,x['after']),(vr,'Retained display mathematics')
  pat=r'\\toprule[\s\S]*?\\bottomrule';assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Tabular content')
  assert re.findall(r'\\label\{[^}]*\}',x['before'])==re.findall(r'\\label\{[^}]*\}',x['after']),(vr,'Labels')
  expected[vr]=x['after']
 for lang in ['thesis2','thesis2-zh']:
  old='\n'.join(x['before'] for x in changes if x['path'].startswith('variants/'+lang+'/'))
  new='\n'.join(x['after'] for x in changes if x['path'].startswith('variants/'+lang+'/'))
  for cmd in ['cite','Cref','cref']:
   pat=r'\\'+cmd+r'(?:\[[^]]*\])?\{[^}]*\}'
   previous=collections.Counter(re.findall(pat,old))
   if cmd=='cref':previous.update(structure_review['added_references'])
   assert previous==collections.Counter(re.findall(pat,new)),('Chapter 3 references',lang,cmd)
  for rel,allowed in removals.items():
   if rel.startswith('variants/'+lang+'/'):
    for block in allowed['blocks']:old=old.replace(block,'',1)
    old=old.replace(allowed['inline'],'',1)
  def structure_values(s):
   s=re.sub(r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}','',s)
   s=re.sub(r'\b(?:E1|FP32|FP64|TF32|int8)\b','',s)
   return collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',s))
  assert structure_values(old)==structure_values(new),('Chapter 3 experimental values',lang)
if chapter4_review:
 names=['04-architecture.tex','04-1-boundaries.tex','04-2-training.tex','04-3-layout.tex','04-4-lifecycle.tex','04-5-construction.tex','04-6-contracts.tex']
 assert set(chapter4_changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in names},'Chapter 4 review scope'
 for rel,h in chapter4_review['unchanged_other_chapters'].items():
  prior=technical_changes.get(rel,ch3_followup_changes.get(rel,ch56_changes.get(rel,cpu_conclusion_changes.get(rel,ch8_changes.get(rel,ch7_changes.get(rel,{})))))).get('before')
  assert (hashlib.sha256(prior.encode()).hexdigest() if prior is not None else historical_sha(r/rel))==h,('Chapter 4 scope spill',rel)
 for x in chapter4_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Chapter 4 before-image',vr)
  for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
   assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,env)
  pat=r'\\\[[\s\S]*?\\\]';assert collections.Counter(re.findall(pat,x['before']))==collections.Counter(re.findall(pat,x['after'])),(vr,'Display mathematics')
  pat=r'\\toprule[\s\S]*?\\bottomrule';assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Tabular content')
  pat=r'\\begin\{figure\}\[.*?\][\s\S]*?\\end\{figure\}|\\par\\medskip\\noindent\\begin\{minipage\}[\s\S]*?\\end\{minipage\}\\par\\medskip'
  assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Figures and fixed tables')
  for cmd in ['label','cite','Cref','cref']:
   pat=r'\\'+cmd+r'(?:\[[^]]*\])?\{[^}]*\}'
   assert collections.Counter(re.findall(pat,x['before']))==collections.Counter(re.findall(pat,x['after'])),(vr,cmd)
  expected[vr]=x['after']
 for lang in ['thesis2','thesis2-zh']:
  previous='\n'.join(x['before'] for x in chapter4_review['changes'] if x['path'].startswith('variants/'+lang+'/'))
  revised='\n'.join(x['after'] for x in chapter4_review['changes'] if x['path'].startswith('variants/'+lang+'/'))
  def chapter4_values(s):
   s=re.sub(r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}','',s)
   s=re.sub(r'\b(?:FP32|FP64|FP16|TF32|int8)\b','',s)
   return collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',s))
  assert chapter4_values(previous)==chapter4_values(revised),('Chapter 4 measured values',lang)
architecture_review=mention_record.get('architecture_figure_followup',{})
if architecture_review:
 assert {x['path'] for x in architecture_review['changes']}=={'variants/'+lang+'/chapters/04-1-boundaries.tex' for lang in ['thesis2','thesis2-zh']},'Architecture follow-up scope'
 for x in architecture_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Architecture before-image',vr)
  for pat in [r'\\(?:label|cite|Cref|cref)(?:\[[^]]*\])?\{[^}]*\}',r'(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$']:
   assert re.findall(pat,x['before'])==re.findall(pat,x['after']),(vr,'Architecture mathematics/references')
  expected[vr]=x['after']
 for rel,source in architecture_review['added_files'].items():
  vr=str(Path(rel).relative_to('variants/thesis2'))
  assert vr not in expected and (r/rel).read_text()==source,('Architecture diagram source',rel)
  expected[vr]=source
if technical_figures:
 for x in technical_figures['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected.get(vr)==x['before'],('Technical-figure before-image',vr)
  expected[vr]=x['after']
if ch3_followup:
 assert set(ch3_followup_changes)=={'variants/'+lang+'/chapters/03-'+name for lang in ['thesis2','thesis2-zh'] for name in ['1-comparisons.tex','2-data.tex','3-measurement.tex','4-frontiers.tex','5-ledger.tex']},'Chapter 3 readability scope'
 for rel,h in ch3_followup['unchanged_source_sha256'].items():
  prior=ch56_changes.get(rel,cpu_conclusion_changes.get(rel,ch8_changes.get(rel,ch7_changes.get(rel,{})))).get('before')
  assert (hashlib.sha256(prior.encode()).hexdigest() if prior is not None else historical_sha(r/rel))==h,('Chapter 3 follow-up scope spill',rel)
 for x in ch3_followup['changes']:
  old,new=x['before'],x['after']
  for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
   assert re.findall(pat,old)==re.findall(pat,new),(x['path'],env)
  for pat in [r'\\\[[\s\S]*?\\\]',r'(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$',r'\\cite(?:\[[^]]*\])?\{[^}]*\}']:
   assert collections.Counter(re.findall(pat,old))==collections.Counter(re.findall(pat,new)),(x['path'],'Mathematics/citations')
  old_tables=re.findall(r'\\toprule([\s\S]*?)\\bottomrule',old);new_tables=re.findall(r'\\toprule([\s\S]*?)\\bottomrule',new)
  if x['path'].endswith('/03-5-ledger.tex'):
   assert len(new_tables)==len(old_tables)+1 and new_tables[1:]==old_tables,'Only the experiment navigation table is added'
   assert [line.split('&',1)[0].strip() for line in new_tables[0].split('\\midrule',1)[1].splitlines() if '&' in line]==['E1','D','T1','T4','T5','A1','A2','A3','B',('R1（记录中为 C1）' if 'thesis2-zh/' in x['path'] else 'R1 (C1 in records)')]
  else:
   assert len(old_tables)==len(new_tables),(x['path'],'Table count')
   for old_t,new_t in zip(old_tables,new_tables):
    get=lambda t:[[re.findall(r'\d+(?:[,.]\d+)*',c) for c in row.split('&')] for row in t.split('\\midrule',1)[1].split('\\\\') if row.strip()]
    assert get(old_t)==get(new_t),(x['path'],'Numerical table cells')
  labels=collections.Counter(re.findall(r'\\label(?:\[[^]]*\])?\{[^}]*\}',old))
  if x['path'].endswith('/03-5-ledger.tex'):labels.update([r'\label{tab:3-campaigns}'])
  assert labels==collections.Counter(re.findall(r'\\label(?:\[[^]]*\])?\{[^}]*\}',new)),(x['path'],'Label change')
  if x['path'].startswith('variants/thesis2/'):
   vr=str(Path(x['path']).relative_to('variants/thesis2'))
   assert expected[vr]==old,('Chapter 3 follow-up before-image',vr)
   expected[vr]=new
ch56_checks={}
if ch56_review:
 from validate_ch56_review import validate as validate_ch56
 ch56_checks=validate_ch56(r,ch56_review,{**final_changes,**ch7_changes,**ch8_changes,**cpu_conclusion_changes})
 for x in ch56_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Chapter 5/6 before-image',vr)
  expected[vr]=x['after']
cpu_conclusion_checks={}
if cpu_conclusion:
 names=['07-evaluation.tex','08-3-validity.tex','09-conclusion.tex']
 assert set(cpu_conclusion_changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in names},'CPU/conclusion scope'
 for rel,digest in cpu_conclusion['unchanged_source_sha256'].items():
  prior=ch8_changes.get(rel,ch7_changes.get(rel,{})).get('before')
  assert (hashlib.sha256(prior.encode()).hexdigest() if prior is not None else historical_sha(r/rel))==digest,('CPU/conclusion scope spill',rel)
 for x in cpu_conclusion['changes']:
  old,new=x['before'],x['after']
  for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
   pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
   assert re.findall(pat,old)==re.findall(pat,new),(x['path'],env)
  for pat in [r'\\\[[\s\S]*?\\\]',r'\\toprule[\s\S]*?\\bottomrule',r'\\label\{[^}]*\}']:
   assert re.findall(pat,old)==re.findall(pat,new),(x['path'],'Protected math/table/labels')
  if x['path'].startswith('variants/thesis2/'):
   vr=str(Path(x['path']).relative_to('variants/thesis2'))
   assert expected[vr]==old,('CPU/conclusion before-image',vr)
   expected[vr]=new
 import math
 cpu_results=cpu_conclusion['historical_cpu']['results']
 targets={'vogue-768':([52,85],[16,32]),'arxiv-768':([56,98],[32]),'openai3-1536':([85,108],[32]),'openai3-3072':([75,77],[16,32])}
 for ds,(limits,threads) in targets.items():
  result=cpu_results[ds];assert result['rounded_range']==limits and result['cpu_threads']==threads,(ds,'CPU provenance')
  ratios=[];cf=result['cpu_front']
  for point in result['ratios']:
   rec=point['recall'];assert cf[0][0]<=rec<=cf[-1][0],(ds,'CPU extrapolation')
   for left,right in zip(cf,cf[1:]):
    if right[0]>=rec:
     weight=(rec-left[0])/(right[0]-left[0]);cq=math.exp(math.log(left[1])+weight*(math.log(right[1])-math.log(left[1])));break
   assert math.isclose(cq,point['cpu_qps'],rel_tol=1e-12),(ds,'CPU frontier interpolation')
   ratio=point['gpu_qps']/cq;assert math.isclose(ratio,point['ratio'],rel_tol=1e-12),(ds,'Historical CPU ratio')
   ratios.append(ratio)
  assert [round(min(ratios)),round(max(ratios))]==limits,(ds,'CPU ratio range')
 cpu_conclusion_checks=dict(exact_before_images_replayed=True,other_sources_unchanged=True,all_equations_proofs_and_table_payloads_preserved=True,historical_cpu_ratios_recomputed=True,thread_count_and_version_scope_explicit=True)
ch8_checks={}
if ch8_review:
 from validate_ch8_review import validate as validate_ch8
 ch8_checks=validate_ch8(r,ch8_review,{**final_changes,**ch7_changes})
 for x in ch8_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Chapter 8 before-image',vr)
  expected[vr]=x['after']
ch7_checks={}
if ch7_review:
 from validate_ch7_review import validate as validate_ch7
 ch7_checks=validate_ch7(r,ch7_review,final_changes)
 for x in ch7_review['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Chapter 7 before-image',vr)
  expected[vr]=x['after']
for rel,s in expected.items():assert historical_text(v/rel)==s,('Unrecorded prior source change',rel)
if final_record:
 from validate_final_review import validate as validate_final
 final_checks=validate_final(r,final_record)
 for x in final_record['changes']:
  if not x['path'].startswith('variants/thesis2/'):continue
  vr=str(Path(x['path']).relative_to('variants/thesis2'))
  assert expected[vr]==x['before'],('Final review before-image',vr)
  expected[vr]=x['after']
 for rel,s in expected.items():assert (v/rel).read_text()==s,('Unrecorded final source change',rel)
assert {str(p.relative_to(v)) for p in v.rglob('*.tex')}==set(expected),'Unrecorded TeX source'
from validate_figure_layout import validate,validate_technical_figures
round_checks=validate(r,round_record,architecture_review,technical_figures)
technical_checks=validate_technical_figures(r,technical_figures,{**final_changes,**ch7_changes,**ch8_changes,**cpu_conclusion_changes,**ch56_changes,**ch3_followup_changes}) if technical_figures else {}
# All body numerical table entries remain unchanged. New component and T1 tables
# are explicitly retained/moved in the structural ledger.
for rel,old in b['variant_source_before'].items():
 if not rel.startswith('chapters/') or rel.endswith('03-5-ledger.tex'):continue
 new=historical_text(v/rel)
 # Column declarations are formatting; the complete numerical/text cell payload is protected.
 pat=r'\\toprule([\s\S]*?)\\bottomrule';old_tables,new_tables=re.findall(pat,old),re.findall(pat,new)
 edit=mention_changes.get('variants/thesis2/'+rel,{}).get('authorised_table_rewording')
 if 'variants/thesis2/'+rel in protocol_paths and rel=='chapters/03-1-comparisons.tex':
  def protocol_numbers(s):
   return [[collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',c)) for c in row.split('&')] for row in s.split('\\midrule',1)[1].split('\\\\') if row.strip()]
  assert len(old_tables)==len(new_tables)==1 and protocol_numbers(old_tables[0])==protocol_numbers(new_tables[0]),'RQ comparison table numerical cells changed'
 elif ch8_review and rel in ['chapters/08-2-negative.tex','chapters/08-3-validity.tex']:
  change=ch8_changes['variants/thesis2/'+rel]
  assert old_tables==re.findall(pat,change['before']) and new_tables==re.findall(pat,change['after']),'Only the recorded Chapter 8 summary table or threat-table wording may change'
 elif ch56_review and rel in ch56_review['authorised_table_rewordings']:
  change=ch56_changes['variants/thesis2/'+rel]
  assert old_tables==re.findall(pat,change['before']) and new_tables==re.findall(pat,change['after']),'Only recorded method-table wording changes'
 elif rel=='chapters/03-4-frontiers.tex' and ch3_followup:
  change=ch3_followup_changes['variants/thesis2/'+rel]
  assert old_tables==re.findall(pat,change['before']) and new_tables==re.findall(pat,change['after']),'Only the recorded tuning-grid wording changes'
 elif 'variants/thesis2/'+rel in protocol_paths and rel=='chapters/04-6-contracts.tex':
  assert len(old_tables)==len(new_tables)==1 and re.sub(r'\bC([01])\b',r'K\1',old_tables[0])==new_tables[0],'Only contract-ID prefixes may change'
 elif 'variants/thesis2/'+rel in background_paths and rel=='chapters/02-7-gap.tex':
  assert len(old_tables)==len(new_tables)==1
  assert re.findall(r'\d+(?:[,.]\d+)*',old_tables[0])==re.findall(r'\d+(?:[,.]\d+)*',new_tables[0])==[], 'The related-work table contains no measured results'
  for method in ['IVF-PQ / OPQ','Fast Scan / Quicker ADC','SONG / CAGRA','BANG','IVF-RaBitQ','Adaptive effort']:assert method in new_tables[0],method
 elif edit:
  assert len(old_tables)==len(new_tables)==1
  validate_intro_table(old_tables[0],new_tables[0],edit,rel)
 else:assert old_tables==new_tables,rel
pdf=r/'build/thesis2/thesis2.pdf';log=pdf.with_suffix('.log').read_text();issues=[s for s in log.splitlines() if re.search(r'Warning|Overfull|Underfull|Missing character|^!',s)];assert not issues,issues
info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);pages=int(re.search(r'^Pages:\s*(\d+)',info,re.M)[1]);t=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True);flat=re.sub(r'\s+','',t)
assert not re.search(r'\[cite:|\?\?',flat)
for term in ['docs/supplementary-evidence','scripts/','assessment/','variants/thesis2','ReproducibilityandExperimentManifest','SupplementaryResultsandCorrectnessChecks']:assert term not in flat,term
fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True).splitlines()[2:]
for f in fonts:
 a=re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$',f);assert a and a[1]=='yes' and 'Type 3' not in f,f
bbox=q/'bbox.html';subprocess.run(['pdftotext','-bbox-layout',str(pdf),str(bbox)],check=True);tree=ET.fromstring(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',bbox.read_text()));proof=collections.Counter();stmt=collections.Counter();positions=[];outside=[]
for i,page in enumerate(tree.findall('.//{*}page'),1):
 width,height=float(page.attrib['width']),float(page.attrib['height']);lines=page.findall('.//{*}line')
 for word in page.findall('.//{*}word'):
  a=word.attrib
  if min(float(a['xMin']),float(a['yMin']))<-.1 or float(a['xMax'])>width+.1 or float(a['yMax'])>height+.1:outside.append((i,word.text))
 for line in lines:
  words=line.findall('{*}word');label=''.join(w.text or '' for w in words)
  if re.match(r'^(?:Lemma|Proposition|Corollary)\d+\.\d+\(',label):stmt[i]+=1
  if label!='Proof.':continue
  proof[i]+=1;x=float(words[0].attrib['xMin']);following=[l for l in lines if float(l.attrib['yMin'])>float(line.attrib['yMax'])];y=min(float(l.attrib['yMin']) for l in following);bodyx=min(float(l.attrib['xMin']) for l in following if float(l.attrib['yMin'])<y+6)
  assert abs(x-27*72/25.4)<1 and abs(x-bodyx)<1,(i,x,bodyx);assert y-float(line.attrib['yMax'])<12
  positions.append(dict(page=i,heading_x=x,body_x=bodyx))
assert not outside,outside
assert sum(proof.values())==6 and proof==stmt,(proof,stmt)
removed_figures=mention_record.get('removed_figure_labels',[])
assert len(removed_figures)==len(set(removed_figures)) and set(removed_figures)<={"fig:1-challenges"},removed_figures
for label in removed_figures:
 assert label not in pdf.with_suffix('.aux').read_text(),('Removed figure still compiled',label)
figs=pdf.with_suffix('.lof').read_text().count('contentsline {figure}');tables=pdf.with_suffix('.lot').read_text().count('contentsline {table}')
expected_figs=round_record['expected']['figures']-len(removed_figures)
expected_tables=round_record['expected']['tables']
if technical_figures:
 assert technical_figures['expected']==dict(figures=expected_figs-3,tables=expected_tables+1,proofs=6),'Recorded figure/table changes'
 expected_figs-=3;expected_tables+=1
 for label in technical_figures['removed_figure_labels']+[technical_figures['converted_figure_label']]:
  assert label not in pdf.with_suffix('.aux').read_text(),('Removed figure still compiled',label)
 assert technical_figures['new_table_label'] in pdf.with_suffix('.aux').read_text()
if ch3_followup:
 assert ch3_followup['expected_table_delta']==1 and ch3_followup['new_table_label']=='tab:3-campaigns'
 expected_tables+=1
 assert 'tab:3-campaigns' in pdf.with_suffix('.aux').read_text()
if ch8_review:
 assert ch8_review['expected_table_delta']==1 and ch8_review['new_table_label']=='tab:8-stopped'
 expected_tables+=1
 assert 'tab:8-stopped' in pdf.with_suffix('.aux').read_text()
assert (figs,tables)==(expected_figs,expected_tables),(figs,tables)
for fact in ['17.78','20.44','0.0006','0.0050','0.0046','0.0294','55,296','13,824','69,120','26.08','22.58','0.641','0.893','1.328','1.316']:assert fact in t,fact
# Confirm no appendix destinations remain; the bibliography ends the document.
dest=subprocess.check_output(['pdfinfo','-dests',str(pdf)],text=True);assert '"appendix.' not in dest
toc=pdf.with_suffix('.toc').read_text();assert '\\numberline {A}' not in toc and '\\numberline {B}' not in toc
front=int(re.search(r'^\s*(\d+)\s+.*"chapter\.1"\s*$',dest,re.M)[1])-1;bib=int(re.search(r'\\contentsline \{chapter\}\{\\nonumberline Bibliography\}\{(\d+)\}',toc)[1])
sys.path.insert(0,str(r/'scripts'));from audit_synthesis import prose_count
active=set()
def visit(rel):
 if rel in active:return
 active.add(rel);s=(v/rel).read_text()
 for name in re.findall(r'\\input\{(variants/thesis2/(?:chapters/[^}]+|frontmatter/abstract))\}',s):visit(name.removeprefix('variants/thesis2/')+'.tex')
visit('main.tex')
counts=dict(m['counts']);counts['historical_body_abstract_after']=counts['body_abstract_after'];counts['body_abstract_after']=sum(prose_count((v/rel).read_text()) for rel in active if rel.startswith('chapters/') or rel=='frontmatter/abstract.tex')
checks=dict(output='thesis2.pdf',pages=pages,body_pages=bib-1,front_pages=front,sha256=sha(pdf),protected_files_unchanged=len(b['protected_files'])-len(missing)-len(set(authorised_document_updates)&set(b['protected_files'])),missing_preexisting_derived_files=missing,original_thesis_unchanged=True,thesis1_unchanged=True,source_edits_exact=True,unmarked_mapped_sentences_preserved=True,theorem_statements_preserved=True,body_numerical_tables_preserved=True,figures=figs,tables=tables,proofs=6,statement_proof_same_page=True,proof_alignment=positions,compiler_issues=[],all_fonts_embedded=True,type3_fonts=0,words_outside_page=0,counts=counts,appendices_removed_from_pdf=True,historical_ledger_unchanged=True,figure_layout_round=round_checks,new_detector_result=None)
checks['technical_figure_review']=technical_checks
if final_record:checks['final_editorial_review']=final_checks
checks['authorised_protected_document_updates']=sorted(authorised_document_updates)
if ch7_review:checks['chapter7_structure_review']=ch7_checks
if ch8_review:checks['chapter8_structure_review']=ch8_checks
if cpu_conclusion:checks['cpu_conclusion_review']=cpu_conclusion_checks
if ch56_review:checks['chapter56_structure_review']=ch56_checks
if ch3_followup:checks['chapter3_readability_followup']=dict(equations_and_proofs_unchanged=True,existing_table_numbers_preserved=True,new_navigation_table=True,unrelated_sources_unchanged=True)
previous=json.loads((v/'checks.json').read_text())
checks['individual_contribution_author_confirmed']=True
checks['individual_contribution_record']='audit/individual-contribution-2026-10-30.json'
checks['targeted_review_record']='audit/review-02a4467-2026-10-30.json'
checks['targeted_review_preserves_proofs_and_tables']=True
checks['frontmatter_review_record']='audit/frontmatter-review-2026-10-30.json'
checks['all_chapter_sources_unchanged_in_frontmatter_round']=True
if mention_record:
 checks['first_mention_review_record']='audit/first-mention-review-2026-10-30.json'
 checks['first_mention_review_preserves_formal_proofs_and_table_numbers']=True
if background_paths:
 checks['chapter2_readability_review']=dict(core_equations_preserved=True,duplicate_sign_derivation_retained_in_chapter4=True,all_measured_tables_unchanged=True,figure_and_table_counts_unchanged=True)
if protocol_paths:
 checks['chapter3_protocol_review']=dict(chapters_1_and_2_unchanged=True,all_display_mathematics_and_proofs_preserved=True,numerical_table_cells_preserved=True,unused_section_alias_removed=True,contract_prefixes_disambiguated=True)
if rq_changes:
 checks['rq_alignment_followup']=dict(names_aligned=True,peak_memory_retained=True,batch_sizes_explicit=True,unlabelled_reference_distinguished_from_quality_baseline=True,numbers_and_formulas_preserved=True)
if previous.get('sha256')==checks['sha256']:
 for key in ['derived_parts','visual_review_pages','completed_date']:
  if key in previous:checks[key]=previous[key]
(v/'checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n');print(json.dumps(checks,indent=2))
