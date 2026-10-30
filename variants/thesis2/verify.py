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
 pat=r'\\toprule([\s\S]*?)\\bottomrule';assert re.findall(pat,old)==re.findall(pat,new),rel
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
figs=pdf.with_suffix('.lof').read_text().count('contentsline {figure}');tables=pdf.with_suffix('.lot').read_text().count('contentsline {table}');assert (figs,tables)==(round_record['expected']['figures'],round_record['expected']['tables']),(figs,tables)
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
if previous.get('sha256')==checks['sha256']:
 for key in ['derived_parts','visual_review_pages','completed_date']:
  if key in previous:checks[key]=previous[key]
(v/'checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n');print(json.dumps(checks,indent=2))
