#!/usr/bin/env python3
"""Fixed official all-Vulkan reference batch; no caller-selected commands."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_batch19 as h
from tools import asciidoc_execution19 as a
from tools import reference_font_repair19 as repair
from tools import reference_links19 as links
from checks19.process_supervisor19 import Cancellation,run_step
p=h.p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--baseline-build',type=Path,required=True);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--runtime-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--cancel-file',type=Path);args=parser.parse_args()
 for name in ('source_root','runtime_root','output','baseline_build'):setattr(args,name,a.execution_path(getattr(args,name)))
 out=args.output;out.mkdir(parents=True,exist_ok=False);report={'status':'BLOCKED','steps':[],'scope':'fixed P4 all-Vulkan368 source cohort; all reference HTML and direct aliases; no semantic proof'}
 oldenv=dict(os.environ);oldcwd=Path.cwd();cancel=Cancellation(args.cancel_file);cancel.install();deadline=time.monotonic()+1800
 owned=[Path(__file__).resolve(),ROOT/'tools/reference_batch19.py',ROOT/'tools/reference_font_repair19.py',ROOT/'tools/reference_links19.py',ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/prose_denominator19.py',ROOT/'tools/prose_generation19.py',ROOT/'checks19/process_supervisor19.py'];own={str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned};report['implementation']=own
 try:
  cancel.check(deadline);snap=out/'implementation';snap.mkdir();
  for f in owned:
   dest=snap/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
  baseline_raw=(args.baseline_build/'report.json').read_bytes();p.need(p.sha(baseline_raw)==repair.REPORT_SHA,'fixed baseline receipt');baseline=json.loads(baseline_raw);baseline_html=args.baseline_build/'source/gen/out/man/html'
  inputs=h.source(args.source_root);matrix=h.expected(args.source_root);runtime=a.runtime(args.runtime_root);report.update(source_tree_sha256=h.SOURCE_TREE_SHA,runtime_sha256=a.RUNTIME_SHA,tests_head=p.git(ROOT,'rev-parse','HEAD').decode().strip(),expected_matrix=matrix)
  rt=args.runtime_root;gem=rt/'usr/share/rubygems-integration/all/gems';ruby=rt/'usr/bin/ruby3.3';adoc=gem/'asciidoctor-2.0.23/bin/asciidoctor';node=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node');libs=out/'ruby-libs';libs.mkdir();(libs/'libruby-3.3.so.3.3').symlink_to(rt/'usr/lib/x86_64-linux-gnu/libruby-3.3.so.3.3')
  os.environ.clear();os.environ.update({'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(out),'LD_LIBRARY_PATH':str(libs),'RUBYLIB':':'.join(map(str,[rt/'usr/lib/ruby/3.3.0',rt/'usr/lib/x86_64-linux-gnu/ruby/3.3.0',gem/'asciidoctor-2.0.23/lib',gem/'rouge-4.5.1/lib'])),'NODE_PATH':str(rt/'usr/share/nodejs'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/usr/lib/python3/dist-packages'})
  report['tools']={str(f):p.sha(f.read_bytes()) for f in (ruby,node,Path('/usr/bin/python3.13'),Path('/usr/bin/make'),Path('/usr/bin/git'),Path('/bin/sh'),Path('/usr/bin/ldd'))};dep=Path('/usr/lib/python3/dist-packages/pyparsing');report['python_dependency']=a.tree(dep)
  def step(label,argv):
   start=time.monotonic();r=run_step(argv,out/(label+'.stdout'),out/(label+'.stderr'),timeout=1700,total_deadline=deadline,cancellation=cancel);r.update(label=label,argv=argv,elapsed_seconds=time.monotonic()-start);report['steps'].append(r);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');p.need(r['returncode']==0 and not any(r[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and r['group_cleanup']['group_gone'],'step failed '+label)
  report['linked_libraries']={}
  for label,file in [('ruby',ruby),('node',node)]:
   step(label+'-ldd',['/usr/bin/ldd',str(file)])
   for line in (out/(label+'-ldd.stdout')).read_text().splitlines():
    for value in line.split():
     if value.startswith('/'):
      f=Path(value).resolve();report['linked_libraries'][str(f)]=p.sha(f.read_bytes())
  source=out/'source';shutil.copytree(args.source_root,source,symlinks=True);html=source/'gen/out/man/html';shutil.rmtree(html);p.need(not html.exists(),'no reused rendered HTML')
  patchfile=source/'config/katex_replace/extension.rb';pre=patchfile.read_bytes();post=repair.patch(pre);(out/'patch-preimage.rb').write_bytes(pre);(out/'patch-postimage.rb').write_bytes(post);patchfile.write_bytes(post);report['patch']={'path':'config/katex_replace/extension.rb','before_sha256':p.sha(pre),'after_sha256':p.sha(post)}
  os.chdir(source)
  nodecode="const r=require('module').createRequire(process.argv[1]);const ids=['escape-string-regexp','he',process.argv[2]];let resolved=ids.map(x=>r.resolve(x));ids.forEach(x=>r(x));console.log(JSON.stringify({resolved,loaded:Object.keys(require.cache)}))"
  step('node-modules',[str(node),'-e',nodecode,str(source/'scripts/translate_math.js'),str(source/'katex/katex.min.js')]);loaded=json.loads((out/'node-modules.stdout').read_bytes());report['node_modules']={}
  for value in loaded['loaded']:
   f=Path(value).resolve();p.need(f.is_relative_to(rt) or f==source/'katex/katex.min.js','unexpected Node module');report['node_modules'][str(f)]=p.sha(f.read_bytes())
  pythoncode="import pyparsing,json;print(json.dumps({'path':pyparsing.__file__}))";step('python-import',['/usr/bin/python3.13','-S','-B','-c',pythoncode]);actual=json.loads((out/'python-import.stdout').read_bytes());p.need(Path(actual['path']).resolve()==dep/'__init__.py','actual pyparsing identity');report['python_import']=actual
  argv=['/usr/bin/python3.13','-S','-B','makeSpec','-spec','all','-version','1.4','PYTHON=/usr/bin/python3.13 -S -B','ASCIIDOC='+str(ruby)+' --disable-gems '+str(adoc),'NODEJS='+str(node),'SPECDATE=2026-11-06T01:31:32Z','SPECREMARK=frozen-fa30d4e-source-replay','-j4','manhtmlpages']
  step('all-reference-html',argv);p.need((out/'all-reference-html.stderr').read_bytes()==b'','official batch diagnostic requires review');report['result']=h.inspect_output(html,matrix,lambda:cancel.check(deadline))
  report['font_assets']={};report['baseline_report_sha256']=repair.REPORT_SHA
  for name in matrix['entities']:
   cancel.check(deadline);original=(baseline_html/(name+'.html')).read_bytes();p.need(p.sha(original)==baseline['result']['entities'][name]['html_sha256'],'baseline HTML changed')
   fonts=repair.page(original,(html/(name+'.html')).read_bytes(),html)
   if report['font_assets']:p.need(fonts==report['font_assets'],'same nine font assets on every page')
   report['font_assets']=fonts
  aliaspaths={'man/html/'+k+'.html':v+'.html' for k,v in matrix['aliases'].items()}
  audit=links.audit(source/'gen/out',['man/html/'+n+'.html' for n in matrix['entities']],aliaspaths,lambda:cancel.check(deadline))
  with (out/'href-occurrences.jsonl').open('w') as f:
   for row in audit.pop('rows'):f.write(json.dumps(row,sort_keys=True)+'\n')
  report['href_audit']=audit;report['font_preload_occurrences']=3553*9
  after=a.tree(source);exclude=lambda d:{k:v for k,v in d.items() if not k.startswith('gen/out/man/html/')};expected_input=dict(inputs);expected_input['config/katex_replace/extension.rb']=after['config/katex_replace/extension.rb'];p.need(patchfile.read_bytes()==post and exclude(after)==exclude(expected_input),'unexpected change outside registered overlay/HTML outputs')
  for name in inputs:
   if name.startswith('gen/out/man/html/'):continue
   p.need((source/name).lstat().st_mode&0o777==(args.source_root/name).lstat().st_mode&0o777,'source/copied mode changed')
  p.need(h.source(args.source_root)==inputs and a.runtime(rt)==runtime,'input changed');p.need(a.tree(dep)==report['python_dependency'],'Python package changed')
  for f,digest in {**report['tools'],**report['linked_libraries'],**report['node_modules']}.items():p.need(p.sha(Path(f).read_bytes())==digest,'runtime identity changed')
  p.need({str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned}==own,'implementation changed');p.need(p.git(ROOT,'rev-parse','HEAD').decode().strip()==report['tests_head'],'head changed');p.need(h.inspect_output(html,matrix,lambda:cancel.check(deadline))==report['result'],'HTML result changed')
  report['artifacts']={f.name:p.sha(f.read_bytes()) for f in out.iterdir() if f.is_file() and f.name!='report.json'};cancel.check(deadline);report['status']='FONT_PRELOAD_REPAIR_VERIFIED_OTHER_LINK_FINDINGS_RETAINED';report['limits']=['fixed isolated upstream patch, not original source or upstream acceptance','all 3553 outputs differ only in nine font hrefs; static WOFF2 presence not browser/font visual proof','remaining navigation/fragment findings retained; no general link completion','actual source snapshots saved under implementation; runtime identity bounded as prior batch']
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  os.chdir(oldcwd);os.environ.clear();os.environ.update(oldenv);cancel.restore();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'steps':len(report['steps'])}));return 0 if report['status']=='FONT_PRELOAD_REPAIR_VERIFIED_OTHER_LINK_FINDINGS_RETAINED' else 2
if __name__=='__main__':raise SystemExit(main())
