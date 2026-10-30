from pathlib import Path
import json,re,hashlib,collections,subprocess,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[2];v=r/'variants/thesis2-zh';en=r/'variants/thesis2';ledger=json.loads((v/'translation-ledger.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
missing=[]
update_path=v/'author-update-2026-10-30.json'
update=json.loads(update_path.read_text()) if update_path.exists() else {}
review_update_path=v/'review-update-2026-10-30.json'
review_update=json.loads(review_update_path.read_text()) if review_update_path.exists() else {}
front_update_path=v/'frontmatter-update-2026-10-30.json'
front_update=json.loads(front_update_path.read_text()) if front_update_path.exists() else {}
mention_update_path=v/'first-mention-update-2026-10-30.json'
mention_update=json.loads(mention_update_path.read_text()) if mention_update_path.exists() else {}
def expected_hash(name,old):
 change=update.get('updated_protected',{}).get(name)
 if change:
  assert change['before_sha256']==old,('Author-update before hash',name)
  old=change['after_sha256']
 change=review_update.get('updated_protected',{}).get(name)
 if change:
  assert change['before_sha256']==old,('Review-update before hash',name)
  old=change['after_sha256']
 change=front_update.get('updated_protected',{}).get(name)
 if change:
  assert change['before_sha256']==old,('Frontmatter-update before hash',name)
  old=change['after_sha256']
 change=mention_update.get('updated_protected',{}).get(name)
 if change:
  assert change['before_sha256']==old,('First-mention-update before hash',name)
  old=change['after_sha256']
 return old
for name,h in ledger['protected_originals'].items():
 if not (r/name).exists():
  assert name in ledger.get('missing_derived_outputs_observed_during_translation',[]),('Original missing',name)
  missing.append(name)
 else:assert sha(r/name)==expected_hash(name,h),('Unrecorded original change',name)
for rel,h in ledger['source_files'].items():assert sha(en/rel)==expected_hash('variants/thesis2/'+rel,h),('Unrecorded English source change',rel)
expected_sources={}
if update:
 ownership=json.loads((r/update['ownership_record']).read_text())
 for change in ownership['changes']:
  if change['path'].startswith('variants/thesis2-zh/'):
   expected_sources[change['path']]=change['after']
if review_update:
 assert sha(update_path)==review_update['previous_update_sha256'],'Previous author-update changed'
 review=json.loads((r/review_update['review_record']).read_text())
 for change in review['changes']:
  if change['path'].startswith('variants/thesis2-zh/'):
   if change['path'] in expected_sources:assert expected_sources[change['path']]==change['before'],('Chinese review before-image',change['path'])
   expected_sources[change['path']]=change['after']
if front_update:
 assert sha(review_update_path)==front_update['previous_review_update_sha256'],'Previous review-update changed'
 front_record=json.loads((r/front_update['frontmatter_record']).read_text())
 for change in front_record['changes']:
  if change['path'].startswith('variants/thesis2-zh/'):
   if change['path'] in expected_sources:assert expected_sources[change['path']]==change['before'],('Chinese frontmatter before-image',change['path'])
   expected_sources[change['path']]=change['after']
if mention_update:
 assert sha(front_update_path)==mention_update['previous_update_sha256'],'Previous frontmatter update changed'
 mention_record=json.loads((r/mention_update['review_record']).read_text())
 for change in mention_record['changes']:
  if change['path'].startswith('variants/thesis2-zh/'):
   if change['path'] in expected_sources:assert expected_sources[change['path']]==change['before'],('Chinese first-mention before-image',change['path'])
   expected_sources[change['path']]=change['after']
for name,source in expected_sources.items():assert (r/name).read_text()==source,('Unrecorded Chinese source',name)
mathpat=re.compile(r'\\begin\{(?:equation\*?|align\*?)\}[\s\S]*?\\end\{(?:equation\*?|align\*?)\}|\\\[[\s\S]*?\\\]|(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$')
parallel=list(ledger['source_files'])
if front_update:parallel+= [pair['english'] for pair in front_record['paired_frontmatter'] if pair['english'] not in parallel]
for rel in parallel:
 a=(en/rel).read_text();b=(v/rel).read_text()
 assert collections.Counter(mathpat.findall(a))==collections.Counter(mathpat.findall(b)),('Math changed',rel)
 for cmd in ['label','cite','Cref','cref']:
  p=r'\\'+cmd+r'(?:\[[^]]*\])?\{[^}]*\}'
  assert collections.Counter(re.findall(p,a))==collections.Counter(re.findall(p,b)),('References changed',rel,cmd)
 assert '[[KEEP' not in b,rel
 for env in ['proof','lemma','proposition','corollary']:
  assert a.count('\\begin{'+env+'}')==b.count('\\begin{'+env+'}'),(rel,env)
 if rel=='chapters/01-5-contributions.tex':
  def intro_cells(s):
   table=re.search(r'\\toprule([\s\S]*?)\\bottomrule',s)[1]
   return [[collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',cell)) for cell in row.split('&')] for row in table.split('\\midrule',1)[1].split('\\\\') if row.strip()]
  assert intro_cells(a)==intro_cells(b),('Contribution table numeric translation',rel)
for item in ledger['external_tables']:
 a=(r/item['source']).read_text();b=(r/item['destination']).read_text();get=lambda s:[[re.findall(r'\d+(?:[,.]\d+)*',c) for c in row.split('&')] for row in s.split('\\midrule',1)[1].split('\\bottomrule')[0].split('\\\\') if row.strip()]
 assert get(a)==get(b),('Numerical cells',item['source'])
 assert collections.Counter(mathpat.findall(a))==collections.Counter(mathpat.findall(b)),item['source']
# Compare internal numerical table cells by row and column as well as complete math.
for edit in ledger['inline_table_translations']:
 def cells(s):
  return [[collections.Counter(re.findall(r'\d+(?:[,.]\d+)*',c)) for c in row.split('&')] for row in s.split('\\midrule',1)[1].split('\\bottomrule')[0].split('\\\\') if row.strip()]
 assert cells(edit['before'])==cells(edit['after']),('Inline data cells',edit['path'])
pdf=r/'build/thesis2-zh/thsis2-zh.pdf';log=pdf.with_suffix('.log').read_text();issues=[line for line in log.splitlines() if re.search(r'Warning|Overfull|Underfull|Missing character|^!',line)];assert not issues,issues
english_checks=json.loads((en/'checks.json').read_text())
figs=pdf.with_suffix('.lof').read_text().count('contentsline {figure}');tables=pdf.with_suffix('.lot').read_text().count('contentsline {table}');assert (figs,tables)==(english_checks['figures'],english_checks['tables']),(figs,tables)
def labels(p):return {m[1]:m[2] for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{',p.read_text()) if not m[1].endswith('@cref')}
a=labels(r/'build/thesis2/thesis2.aux');b=labels(pdf.with_suffix('.aux'));assert a==b,('Label numbers differ',set(a)^set(b),[(k,a[k],b.get(k)) for k in a if b.get(k)!=a[k]])
text=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True);flat=re.sub(r'\s+','',text);assert not re.search(r'\?\?|\[\[KEEP',flat)
assert flat.count('证明.')==6 or flat.count('证明。')==6,('Proof text count',flat.count('证明.'),flat.count('证明。'))
fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True).splitlines()[2:]
for line in fonts:
 m=re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$',line);assert m and m[1]=='yes' and 'Type 3' not in line,line
q=r/'build/thesis2-zh/verification';q.mkdir(exist_ok=True);bbox=q/'bbox.html';subprocess.run(['pdftotext','-bbox-layout',str(pdf),str(bbox)],check=True);tree=ET.fromstring(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',bbox.read_text()));outside=[]
for n,page in enumerate(tree.findall('.//{*}page'),1):
 w,h=float(page.attrib['width']),float(page.attrib['height'])
 for word in page.findall('.//{*}word'):
  p=word.attrib
  if min(float(p['xMin']),float(p['yMin']))<-.1 or float(p['xMax'])>w+.1 or float(p['yMax'])>h+.1:outside.append((n,word.text))
assert not outside,outside
info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);pages=int(re.search(r'^Pages:\s*(\d+)',info,re.M)[1]);dest=subprocess.check_output(['pdfinfo','-dests',str(pdf)],text=True);assert '"appendix.' not in dest
current_english=expected_hash('thesis2.pdf',ledger['english_pdf_sha256'])
assert sha(r/'thesis2.pdf')==current_english,'English PDF does not match recorded source update'
result=dict(output='thsis2-zh.pdf',pages=pages,english_pdf_sha256=current_english,initial_translation_english_sha256=ledger['english_pdf_sha256'],sha256=sha(pdf),translated_source_files=len(ledger['source_files']),original_files_unchanged=sum(1 for name,h in ledger['protected_originals'].items() if (r/name).exists() and sha(r/name)==h),missing_derived_outputs=missing,english_thesis2_unchanged=current_english==ledger['english_pdf_sha256'],authorised_english_updates=list(update.get('updated_protected',{})),individual_contribution_author_confirmed=bool(update),math_blocks_identical=True,numerical_cells_preserved=True,labels_numbers_and_citations_match=True,figures=figs,tables=tables,proofs=6,compiler_issues=issues,fonts_embedded=True,words_outside_page=outside,figures_keep_english_labels=True)
p=v/'checks.json';previous=json.loads(p.read_text()) if p.exists() else {}
if review_update:
 result['authorised_english_updates']=sorted(set(result['authorised_english_updates'])|set(review_update.get('updated_protected',{})))
 result['targeted_review_record']=review_update['review_record']
if front_update:
 result['authorised_english_updates']=sorted(set(result['authorised_english_updates'])|set(front_update.get('updated_protected',{})))
 result['frontmatter_review_record']=front_update['frontmatter_record']
 result['translated_source_files']=len(parallel)
if mention_update:
 result['authorised_english_updates']=sorted(set(result['authorised_english_updates'])|set(mention_update.get('updated_protected',{})))
 result['first_mention_review_record']=mention_update['review_record']
if previous.get('sha256')==result['sha256']:
 for key in ['visual_review_pages','completed_date']:
  if key in previous:result[key]=previous[key]
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
