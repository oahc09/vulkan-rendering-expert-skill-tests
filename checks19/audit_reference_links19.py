#!/usr/bin/env python3
"""Read-only static href audit of fixed P5 outputs; findings are not build failure."""
import argparse,json,os,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_links19 as h
from tools import reference_batch19 as batch
from tools import asciidoc_execution19 as a
from checks19.process_supervisor19 import Cancellation
p=h.p

def regular_json(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  st=os.fstat(fd);p.need(stat.S_ISREG(st.st_mode) and st.st_size<16000000,'bounded regular JSON');raw=os.read(fd,16000000);p.need(len(raw)==st.st_size,'JSON read size');return raw,json.loads(raw,object_pairs_hook=a.unique)
 finally:os.close(fd)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--build-root',type=Path,required=True);parser.add_argument('--expected-report-sha',required=True);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--cancel-file',type=Path);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
 report={'status':'BLOCKED','authority':'READ_ONLY_STATIC_AUDIT_NOT_NEW_RENDER'};cancel=Cancellation(args.cancel_file);cancel.install();deadline=time.monotonic()+300;ownfiles=[Path(__file__).resolve(),ROOT/'tools/reference_links19.py',ROOT/'tools/reference_batch19.py',ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/prose_denominator19.py',ROOT/'tools/prose_generation19.py',ROOT/'checks19/process_supervisor19.py'];own={str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in ownfiles}
 try:
  cancel.check(deadline);root=args.build_root.resolve();source=root/'source';report_raw,build=regular_json(root/'report.json');p.need(p.sha(report_raw)==args.expected_report_sha,'externally expected original build report digest');p.need(build.get('status')=='FIXED_ALL_REFERENCE_HTML_AND_ALIASES_RECHECKED' and build.get('source_tree_sha256')==batch.SOURCE_TREE_SHA,'fixed original build scope')
  inputs=batch.source(args.source_root.resolve());actual=a.tree(source);project=lambda v:{k:d for k,d in v.items() if not k.startswith('gen/out/man/html/')};p.need(project(actual)==project(inputs),'fixed source/fullspec/assets projection')
  matrix=batch.expected(source);render=batch.inspect_output(source/'gen/out/man/html',matrix,lambda:cancel.check(deadline));p.need(build['result']['aliases']==render['aliases'],'build aliases differ')
  for name,row in render['entities'].items():p.need(all(build['result']['entities'][name][k]==row[k] for k in ('source_sha256','html_sha256','bytes')),'original rendered page changed')
  pages=['man/html/'+n+'.html' for n in matrix['entities']];aliases={'man/html/'+n+'.html':v+'.html' for n,v in matrix['aliases'].items()};result=h.audit(source/'gen/out',pages,aliases,lambda:cancel.check(deadline))
  rows=result.pop('rows');occurrences=args.output/'occurrences.jsonl'
  with occurrences.open('x') as stream:
   for row in rows:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
  findings={}
  for row in rows:
   if row['status']in ('LOCAL_RESOLVED','EXTERNAL_NOT_FETCHED'):continue
   key=p.canon({'role':row['role'],'status':row['status'],'href':row['href'],'target':row.get('target'),'fragment':row.get('fragment')}).decode()
   if key not in findings:findings[key]={'role':row['role'],'status':row['status'],'href':row['href'],'target':row.get('target'),'fragment':row.get('fragment'),'occurrences':0,'example':{'page':row['page'],'line':row['line'],'column':row['column']},'full_spec_candidate':row.get('same_fragment_in_full_spec',False)}
   findings[key]['occurrences']+=1
  report.update(result,original_build_report_sha256=p.sha(report_raw),original_build_implementation=build['implementation'],implementation=own,findings=list(findings.values()),occurrences_sha256=p.sha(occurrences.read_bytes()),occurrences_file='occurrences.jsonl',alias_scope={'registered':477,'followed_only_exact_direct_entities':True},external_links_fetched=0)
  # Two concrete missing navigation pages originate as internal-anchor xrefs.
  references=[('chapters/memory.adoc',[145,223]),('appendices/VK_KHR_shader_float_controls.adoc',[90,125]),('config/katex_replace/extension.rb',list(range(24,33)))];report['source_context']=[]
  for name,lines in references:
   raw=(source/name).read_bytes();parts=raw.decode().splitlines();report['source_context'].append({'path':name,'sha256':p.sha(raw),'lines':[{'number':n,'text':parts[n-1]} for n in lines],'authority':'SOURCE_LOCATION_NOT_AUTOMATIC_REPAIR'})
  cancel.check(deadline);p.need(regular_json(root/'report.json')[0]==report_raw,'original report changed');p.need(a.tree(source)==actual,'render/source tree changed');p.need(batch.source(args.source_root.resolve())==inputs,'input source cohort changed');p.need({str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in ownfiles}==own,'audit implementation changed')
 except Exception as e:report['status']='BLOCKED';report['error']=type(e).__name__+': '+str(e)
 finally:cancel.restore();(args.output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'status':report['status'],'href_occurrences':report.get('href_occurrences')}));return 0 if report['status']in ('PARTIAL_WITH_FINDINGS','LOCAL_HREFS_RESOLVED_EXTERNAL_UNVERIFIED') else 2
if __name__=='__main__':raise SystemExit(main())
