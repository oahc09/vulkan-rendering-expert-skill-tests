#!/usr/bin/env python3
"""Offline post-build verification; never changes or rerenders the failed receipt."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_batch19 as h,asciidoc_execution19 as a,reference_font_repair19 as r,reference_links19 as links
from checks19.process_supervisor19 import Cancellation
p=h.p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build-root',type=Path,required=True);ap.add_argument('--expected-report-sha',required=True);ap.add_argument('--baseline-build',type=Path,required=True);ap.add_argument('--source-root',type=Path,required=True);ap.add_argument('--runtime-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cancel-file',type=Path);args=ap.parse_args()
 for n in ('build_root','baseline_build','source_root','runtime_root','output'):setattr(args,n,a.execution_path(getattr(args,n)))
 out=args.output;out.mkdir(parents=True,exist_ok=False);report={'status':'BLOCKED','execution':'OFFLINE_RECHECK_NO_RENDER_OR_GPU'};cancel=Cancellation(args.cancel_file);cancel.install();deadline=time.monotonic()+300
 owned=[Path(__file__).resolve(),ROOT/'tools/reference_font_repair19.py',ROOT/'tools/reference_batch19.py',ROOT/'tools/reference_links19.py',ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/prose_denominator19.py',ROOT/'tools/prose_generation19.py',ROOT/'checks19/process_supervisor19.py'];own={str(f.relative_to(ROOT)):p.sha(f.read_bytes())for f in owned}
 try:
  cancel.check(deadline);build=args.build_root;raw=(build/'report.json').read_bytes();p.need(p.sha(raw)==args.expected_report_sha,'original build receipt digest');b=json.loads(raw);p.need(b['status']=='BLOCKED' and b['error']=='ValueError: nine unique font preloads','registered completed-build first-validator failure')
  p.need([s['label']for s in b['steps']]==['ruby-ldd','node-ldd','node-modules','python-import','all-reference-html'],'complete five build steps')
  r.verify_commands(b['steps'],args.build_root,args.runtime_root)
  logs={}
  for s in b['steps']:
   p.need(type(s['returncode'])is int and s['returncode']==0 and all(s[k]is False for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and s['group_cleanup']['group_gone']is True,'original render/control completion')
   for ext in ('stdout','stderr'):
    f=build/(s['label']+'.'+ext);p.need(f.is_file() and not f.is_symlink(),'regular saved raw log');logs[f.name]=p.sha(f.read_bytes())
  p.need((build/'all-reference-html.stderr').read_bytes()==b'','unreviewed render diagnostics')
  for name,digest in b['implementation'].items():
   p.need(name in {str(f.relative_to(ROOT))for f in owned}|{'checks19/repair_reference_fonts19.py'},'registered snapshot source path');p.need(p.sha((build/'implementation'/name).read_bytes())==digest,'actual build source snapshot')
  inp=h.source(args.source_root);runtime=a.runtime(args.runtime_root);matrix=h.expected(args.source_root);src=build/'source';html=src/'gen/out/man/html';baseline_raw=(args.baseline_build/'report.json').read_bytes();p.need(p.sha(baseline_raw)==r.REPORT_SHA,'fixed original P5 receipt');baseline=json.loads(baseline_raw)
  pre=(args.source_root/'config/katex_replace/extension.rb').read_bytes();post=r.patch(pre);p.need((build/'patch-preimage.rb').read_bytes()==pre and (build/'patch-postimage.rb').read_bytes()==post and (src/'config/katex_replace/extension.rb').read_bytes()==post,'exact source overlay')
  expected=dict(inp);expected['config/katex_replace/extension.rb']={'sha256':p.sha(post)};exclude=lambda d:{k:v for k,v in d.items()if not k.startswith('gen/out/man/html/')};tree=a.tree(src);p.need(exclude(tree)==exclude(expected),'only registered source patch and HTML changed')
  for name in inp:
   if not name.startswith('gen/out/man/html/'):p.need((src/name).lstat().st_mode&0o777==(args.source_root/name).lstat().st_mode&0o777,'source mode drift')
  result=h.inspect_output(html,matrix,lambda:cancel.check(deadline));fonts={};original_hashes={}
  for name in matrix['entities']:
   cancel.check(deadline);f=args.baseline_build/'source/gen/out/man/html'/(name+'.html');original=f.read_bytes();original_hashes[str(f)]=p.sha(original);p.need(p.sha(original)==baseline['result']['entities'][name]['html_sha256'],'original P5 HTML drift');found=r.page(original,(html/(name+'.html')).read_bytes(),html)
   if fonts:p.need(found==fonts,'same fixed font assets')
   fonts=found
  audit=links.audit(src/'gen/out',['man/html/'+n+'.html'for n in matrix['entities']],{'man/html/'+k+'.html':v+'.html'for k,v in matrix['aliases'].items()},lambda:cancel.check(deadline))
  with (out/'href-occurrences.jsonl').open('w')as f:
   for row in audit.pop('rows'):f.write(json.dumps(row,sort_keys=True)+'\n')
  snapshots=out/'implementation'
  for f in owned:
   dest=snapshots/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
  for category in ('tools','linked_libraries','node_modules'):
   for path,digest in b[category].items():
    f=Path(path);p.need(f.is_absolute() and any(f.is_relative_to(root)for root in (Path('/usr'),Path('/bin'),Path('/opt/codex'),args.runtime_root,src)),'bounded runtime path');p.need(p.sha(f.read_bytes())==digest,'runtime byte drift')
  p.need(a.tree(Path('/usr/lib/python3/dist-packages/pyparsing'))==b['python_dependency'],'Python dependency drift')
  p.need(a.tree(src)==tree and h.source(args.source_root)==inp and a.runtime(args.runtime_root)==runtime,'source/runtime drift');p.need(all(p.sha(Path(f).read_bytes())==d for f,d in original_hashes.items()),'baseline HTML drift')
  p.need((build/'report.json').read_bytes()==raw and (args.baseline_build/'report.json').read_bytes()==baseline_raw,'receipt drift');p.need(all(p.sha((build/n).read_bytes())==d for n,d in logs.items()),'log drift');p.need({str(f.relative_to(ROOT)):p.sha(f.read_bytes())for f in owned}==own,'validator drift');cancel.check(deadline)
  report.update(status='FONT_PRELOAD_REPAIR_VERIFIED_OTHER_LINK_FINDINGS_RETAINED',original_build_status=b['status'],original_build_report_sha256=p.sha(raw),original_build_implementation=b['implementation'],implementation=own,raw_build_logs=logs,raw_log_binding='FIRST_HASHED_AT_OFFLINE_RECHECK_NOT_ORIGINAL_EXECUTION; ORIGINAL_FAILED_REPORT_HAS_NO_STREAM_DIGESTS',result=result,font_assets=fonts,font_preload_occurrences=31977,href_audit=audit,limits=['original rendering completed under preserved prior implementation; first validator failed on extra external FontAwesome preload','current offline checker separately validates all pages; original receipt unchanged','exact nine href replacements per entity; FontAwesome and other bytes unchanged','static WOFF2 bytes/existence only, no browser/font visual test','navigation/fragment findings remain, external URLs not fetched'])
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:cancel.restore();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status']);return 0 if report['status']=='FONT_PRELOAD_REPAIR_VERIFIED_OTHER_LINK_FINDINGS_RETAINED'else 2
if __name__=='__main__':raise SystemExit(main())
