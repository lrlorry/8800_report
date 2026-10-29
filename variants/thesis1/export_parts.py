#!/usr/bin/env python3
"""Export the same two chapter scopes as the supplied highlight reports."""
from pathlib import Path
import subprocess,re,json,shutil,hashlib,collections
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/thesis1/exports';build.mkdir(parents=True,exist_ok=True)
source=ROOT/'thesis1.pdf'
info=subprocess.check_output(['pdfinfo',str(source)],text=True)
total=int(re.search(r'^Pages:\s*(\d+)',info,re.M)[1])
dest=subprocess.check_output(['pdfinfo','-dests',str(source)],text=True)
split=int(re.search(r'^\s*(\d+)\s+.*"chapter\.6"\s*$',dest,re.M)[1])
source_text=subprocess.check_output(['pdftotext',str(source),'-'],text=True).split('\f')[:-1]
records=[]
for name,first,last in [('thesis1-part1',1,split-1),('thesis1-part2',split,total)]:
 tex='\\documentclass[a4paper]{article}\n\\usepackage{pdfpages}\n\\begin{document}\\pagestyle{empty}\n'
 tex+='\\includepdf[pages='+str(first)+'-'+str(last)+',fitpaper=true,pagecommand={}]{thesis1.pdf}\n\\end{document}\n'
 path=build/(name+'.tex');path.write_text(tex)
 done=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory='+str(build),str(path)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 assert done.returncode==0,done.stdout.decode(errors='replace')[-2000:]
 target=ROOT/(name+'.pdf');shutil.copyfile(build/target.name,target)
 pages=subprocess.check_output(['pdftotext',str(target),'-'],text=True).split('\f')[:-1]
 assert len(pages)==last-first+1
 for i,text in enumerate(pages):
  chars=lambda t:collections.Counter(re.sub(r'\s+','',t))
  assert chars(text)==chars(source_text[first-1+i]),(name,i)
 records.append(dict(path=target.name,pages=len(pages),source_physical_pages=[first,last],sha256=hashlib.sha256(target.read_bytes()).hexdigest(),page_text_preserved=True))
p=ROOT/'variants/thesis1/checks.json';check=json.loads(p.read_text());check['derived_parts']=records
p.write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(records,indent=2))
