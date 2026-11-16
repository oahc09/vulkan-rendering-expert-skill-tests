#!/usr/bin/env python3
"""Offline stronger content/inventory gate; never reruns or relabels the build."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_batch19 as h
from tools import asciidoc_execution19 as a
p=h.p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--build-output',type=Path,required=True);parser.add_argument('--expected-report-sha',required=True);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
 report={'status':'BLOCKED','authority':'OFFLINE_RECHECK_NOT_NEW_BUILD'}
 try:
  root=args.build_output.resolve();file=root/'report.json';p.need(file.is_file() and not file.is_symlink() and file.stat().st_size<16000000,'build report regular bounded file');raw=file.read_bytes();p.need(p.sha(raw)==args.expected_report_sha,'trusted expected build report digest');build=json.loads(raw,object_pairs_hook=a.unique)
  p.need(build.get('status')=='FIXED_ALL_REFERENCE_HTML_AND_ALIASES_RECHECKED' and build.get('source_tree_sha256')==h.SOURCE_TREE_SHA,'fixed build scope')
  labels=['ruby-ldd','node-ldd','node-modules','python-import','all-reference-html','missing-target','wrong-regular-alias'];p.need([s['label'] for s in build['steps']]==labels,'exact original build step set')
  for step in build['steps']:p.need(type(step['returncode'])is int and step['returncode']==0 and step['group_cleanup']['group_gone'] is True and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')),'original step failed')
  for name,digest in build['artifacts'].items():
   p.need(Path(name).name==name and name not in ('.','..'),'artifact basename only');artifact=root/name;p.need(artifact.is_file() and not artifact.is_symlink() and p.sha(artifact.read_bytes())==digest,'build artifact changed')
  inputs=h.source(args.source_root.resolve());source=root/'source';actual=a.tree(source);exclude=lambda d:{k:v for k,v in d.items() if not k.startswith('gen/out/man/html/')};p.need(exclude(inputs)==exclude(actual),'source/generated input projection changed')
  matrix=h.expected(source);result=h.inspect_output(source/'gen/out/man/html',matrix)
  old=build['result'];p.need(old['aliases']==result['aliases'] and set(old['entities'])==set(result['entities']),'original result inventory differs')
  for name,row in result['entities'].items():p.need(all(old['entities'][name][k]==row[k] for k in ('source_sha256','html_sha256','bytes')),'original HTML bytes changed')
  for label in ('missing-target','wrong-regular-alias'):
   rejected=False
   try:h.inspect_output(root/label,matrix)
   except ValueError:rejected=True
   p.need(rejected,'original HOST control unexpectedly accepted')
  impl=[Path(__file__).resolve(),ROOT/'tools/reference_batch19.py',ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/prose_denominator19.py'];report.update(original_report_sha256=p.sha(raw),original_build_implementation=build['implementation'],recheck_implementation={str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in impl},result=result,limitations=['original runtime/build commands not reexecuted','source-derived body/section presence is not full semantic or visual correctness','no internal cross-page hyperlink scan'])
  p.need(file.read_bytes()==raw,'build report changed during recheck');report['status']='EXISTING_BUILD_CONTENT_AND_ALIASES_RECHECKED'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status']);return 0 if report['status']=='EXISTING_BUILD_CONTENT_AND_ALIASES_RECHECKED' else 2
if __name__=='__main__':raise SystemExit(main())
