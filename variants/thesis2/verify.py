from pathlib import Path
import json,re,hashlib,collections,sys,subprocess,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[2];v=r/'variants/thesis2';q=r/'build/thesis2/verification';q.mkdir(parents=True,exist_ok=True);b=json.loads((v/'audit/baseline.json').read_text());m=json.loads((v/'audit/edits.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda s:re.sub(r'\s+',' ',s).strip()
missing=[]
for rel,h in b['protected_files'].items():
 if not (r/rel).exists():
  assert rel in ['thesis1-part1.pdf','thesis1-part2.pdf'],('Protected file missing',rel)
  missing.append(rel)
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
background=mention_record.get('background_review',{})
background_paths=set(background.get('paths',[]))
if background_paths:
 assert background_paths=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in ['02-background.tex','02-1-objective.tex','02-2-hierarchy.tex','02-3-jhq.tex','02-4-gpu.tex','02-5-graphs.tex','02-6-quantised.tex','02-7-gap.tex']},'Chapter-2 scope'
 assert sha(v/'chapters/04-2-training.tex')==background['unchanged_later_sign_derivation_sha256'],'Retained sign derivation changed'
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
for rel,h in mention_record.get('unchanged_source_hashes',{}).items():assert sha(r/rel)==h,('Unrecorded readability source change',rel)
for group in ['chapter_sources_unchanged','shared_frontmatter_unchanged','historical_ledgers_unchanged','frozen_style_previews']:
 for rel,h in front_record[group].items():
  before=mention_changes.get(rel,{}).get('before')
  observed=hashlib.sha256(before.encode()).hexdigest() if before is not None else sha(r/rel)
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
 if x['path'] in background_paths:
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
for rel,s in expected.items():assert (v/rel).read_text()==s,('Unrecorded source change',rel)
assert {str(p.relative_to(v)) for p in v.rglob('*.tex')}==set(expected),'Unrecorded TeX source'
from validate_figure_layout import validate
round_checks=validate(r,round_record)
# All body numerical table entries remain unchanged. New component and T1 tables
# are explicitly retained/moved in the structural ledger.
for rel,old in b['variant_source_before'].items():
 if not rel.startswith('chapters/') or rel.endswith('03-5-ledger.tex'):continue
 new=(v/rel).read_text()
 # Column declarations are formatting; the complete numerical/text cell payload is protected.
 pat=r'\\toprule([\s\S]*?)\\bottomrule';old_tables,new_tables=re.findall(pat,old),re.findall(pat,new)
 edit=mention_changes.get('variants/thesis2/'+rel,{}).get('authorised_table_rewording')
 if 'variants/thesis2/'+rel in background_paths and rel=='chapters/02-7-gap.tex':
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
figs=pdf.with_suffix('.lof').read_text().count('contentsline {figure}');tables=pdf.with_suffix('.lot').read_text().count('contentsline {table}');assert (figs,tables)==(round_record['expected']['figures']-len(removed_figures),round_record['expected']['tables']),(figs,tables)
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
checks=dict(output='thesis2.pdf',pages=pages,body_pages=bib-1,front_pages=front,sha256=sha(pdf),protected_files_unchanged=len(b['protected_files'])-len(missing),missing_preexisting_derived_files=missing,original_thesis_unchanged=True,thesis1_unchanged=True,source_edits_exact=True,unmarked_mapped_sentences_preserved=True,theorem_statements_preserved=True,body_numerical_tables_preserved=True,figures=figs,tables=tables,proofs=6,statement_proof_same_page=True,proof_alignment=positions,compiler_issues=[],all_fonts_embedded=True,type3_fonts=0,words_outside_page=0,counts=counts,appendices_removed_from_pdf=True,historical_ledger_unchanged=True,figure_layout_round=round_checks,new_detector_result=None)
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
if previous.get('sha256')==checks['sha256']:
 for key in ['derived_parts','visual_review_pages','completed_date']:
  if key in previous:checks[key]=previous[key]
(v/'checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n');print(json.dumps(checks,indent=2))
