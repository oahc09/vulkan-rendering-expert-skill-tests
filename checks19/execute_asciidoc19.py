#!/usr/bin/env python3
import argparse,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import asciidoc_execution19 as h
from checks19.process_supervisor19 import Cancellation,run_step
p=h.p
def main():
 a=argparse.ArgumentParser();a.add_argument('--docs-git',type=Path,required=True);a.add_argument('--runtime-root',type=Path,required=True);a.add_argument('--generated-root',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--cancel-file',type=Path);a=a.parse_args()
 for name in ('output','runtime_root','generated_root','docs_git'):setattr(a,name,h.execution_path(getattr(a,name)))
 a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();a.runtime_root=a.runtime_root.resolve();a.generated_root=a.generated_root.resolve();a.docs_git=a.docs_git.resolve()
 report={'status':'BLOCKED','steps':[],'closure_status':'PARTIAL_SINGLE_CONFIGURATION_NOT_ALL_P'};oldenv=dict(os.environ);oldcwd=Path.cwd();cancel=Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+240
 owned=[Path(__file__).resolve(),ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/asciidoc_observer19.rb',ROOT/'tools/prose_generation19.py',ROOT/'tools/prose_denominator19.py',ROOT/'checks19/process_supervisor19.py'];own={str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned};report['implementation']=own
 try:
  report['tests_head']=p.git(ROOT,'rev-parse','HEAD').decode().strip();rt=h.runtime(a.runtime_root);gen=h.generated(a.generated_root);files=p.load(a.docs_git)
  report['runtime_tree_sha256']=h.RUNTIME_SHA;report['generated_sha256']=h.GENERATED_SHA;report['source_commit']=p.COMMIT
  libs=a.output/'ruby-libs';libs.mkdir();(libs/'libruby-3.3.so.3.3').symlink_to(a.runtime_root/'usr/lib/x86_64-linux-gnu/libruby-3.3.so.3.3')
  ruby=a.runtime_root/'usr/bin/ruby3.3';gem=a.runtime_root/'usr/share/rubygems-integration/all/gems';node=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node');adoc=gem/'asciidoctor-2.0.23/bin/asciidoctor'
  env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(a.output),'LD_LIBRARY_PATH':str(libs),'RUBYLIB':':'.join(map(str,[a.runtime_root/'usr/lib/ruby/3.3.0',a.runtime_root/'usr/lib/x86_64-linux-gnu/ruby/3.3.0',gem/'asciidoctor-2.0.23/lib',gem/'rouge-4.5.1/lib'])),'NODE_PATH':str(a.runtime_root/'usr/share/nodejs'),'PYTHONDONTWRITEBYTECODE':'1'}
  os.environ.clear();os.environ.update(env);report['tools']={str(f):p.sha(f.read_bytes()) for f in [ruby,node,Path('/usr/bin/python3.13'),Path('/usr/bin/make'),Path('/usr/bin/git'),Path('/bin/sh')]}
  def step(label,argv,expected=0):
   result=run_step(argv,a.output/(label+'.stdout'),a.output/(label+'.stderr'),timeout=90,total_deadline=deadline,cancellation=cancel);result.update(label=label,argv=argv);report['steps'].append(result)
   p.need(result['returncode']==expected and not any(result[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and result['group_cleanup']['group_gone'],'step failed '+label)
  step('ruby-ldd',['/usr/bin/ldd',str(ruby)])
  step('node-ldd',['/usr/bin/ldd',str(node)])
  report['linked_libraries']={}
  for line in ((a.output/'ruby-ldd.stdout').read_text()+(a.output/'node-ldd.stdout').read_text()).splitlines():
   fields=line.split();paths=[x for x in fields if x.startswith('/')]
   for path in paths:
    f=Path(path).resolve();report['linked_libraries'][str(f)]=p.sha(f.read_bytes())
  html=[]
  for label in ('baseline','observed'):
   cancel.check(deadline);root=a.output/label;root.mkdir()
   for name,f in files.items():
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(f['raw']);dst.chmod(0o755 if f['mode']=='100755' else 0o644)
   shutil.copytree(a.generated_root,root/'gen');os.chdir(root)
   # Preserve generated targets newer than freshly exported source, so this step
   # renders the already independently verified fragments, not an implicit rebuild.
   for name in files:os.utime(root/name,(1,1))
   extra=''
   if label=='observed':extra=' -r '+str(ROOT/'tools/asciidoc_observer19.rb');os.environ['VULKAN_ADOC_TRACE']=str(a.output/'trace.jsonl')
   else:os.environ.pop('VULKAN_ADOC_TRACE',None)
   if label=='baseline':
    nodecode="const r=require('module').createRequire(process.argv[1]);const ids=['escape-string-regexp','he',process.argv[2]];const paths=ids.map(x=>r.resolve(x));ids.forEach(x=>r(x));console.log(JSON.stringify({resolved:paths,loaded:Object.keys(require.cache)}));"
    step('node-modules',[str(node),'-e',nodecode,str(root/'scripts/translate_math.js'),str(root/'katex/katex.min.js')])
    observed=json.loads((a.output/'node-modules.stdout').read_bytes());report['node_modules']={}
    for name in observed['loaded']:
     f=Path(name).resolve();p.need(f.is_relative_to(a.runtime_root) or f==root/'katex/katex.min.js','unexpected Node module');report['node_modules'][name]=p.sha(f.read_bytes())
    report['node_resolved']=observed['resolved']
   command=str(ruby)+' --disable-gems'+extra+' '+str(adoc)
   argv=['/usr/bin/make','-j1','VULKAN_API=vulkan','EXTENSIONS=','VERSIONS='+' '.join(h.g.ATTRIBUTES),'ASCIIDOC='+command,'NODEJS='+str(node),'SPECDATE=2026-11-06T01:31:32Z','SPECREMARK=frozen-fa30d4e-source-replay','html']
   step(label,argv);p.need((a.output/(label+'.stderr')).read_bytes()==b'','render diagnostic must be reviewed');html.append((root/'gen/out/html/vkspec.html').read_bytes())
  # Explicit overlays are separate from both untouched source cohorts.
  report['controls']={}
  for kind in ('active_missing','inactive_missing','tag_changed'):
   root=a.output/('control-'+kind);shutil.copytree(a.output/'baseline',root);os.chdir(root)
   output=root/'gen/out/html/vkspec.html';output.unlink()
   relative='gen/api/structs/VkMemoryDedicatedRequirements.adoc' if kind=='active_missing' else 'gen/meta/VK_AMD_buffer_marker.adoc' if kind=='inactive_missing' else 'chapters/devsandqueues.adoc'
   target=root/relative;before=target.read_bytes()
   if kind=='tag_changed':
    lines=before.splitlines(keepends=True);p.need(lines[589]==b'// tag::VK_KHR_external_memory_capabilities-properties[]\n' and lines[591]==b'    representing a universally unique identifier for the device.\n','fixed selected tag line');lines[591]=b'    representing a HOST CONTROL MUTANT identifier for the device.\n';target.write_bytes(b''.join(lines))
    os.utime(target,(1,1))
   else:target.unlink()
   os.environ.pop('VULKAN_ADOC_TRACE',None)
   control_command=str(ruby)+' --disable-gems '+str(adoc)
   if kind=='tag_changed':
    os.environ['VULKAN_ADOC_TRACE']=str(a.output/'tag-control-trace.jsonl');control_command=str(ruby)+' --disable-gems -r '+str(ROOT/'tools/asciidoc_observer19.rb')+' '+str(adoc)
   control_argv=[x for x in argv if not x.startswith('ASCIIDOC=')]+['ASCIIDOC='+control_command]
   step(kind,control_argv,2 if kind=='active_missing' else 0)
   stderr=(a.output/(kind+'.stderr')).read_text()
   if kind=='active_missing':p.need('include file not found:' in stderr and 'VkMemoryDedicatedRequirements.adoc' in stderr and not output.exists(),'active missing include not detected')
   elif kind=='inactive_missing':p.need(output.read_bytes()==html[0] and stderr=='','inactive removal changed core output')
   else:p.need(output.read_bytes()!=html[0] and b'HOST CONTROL MUTANT' in output.read_bytes() and stderr=='','actual tagged mutation did not change rendered HTML')
   if kind=='tag_changed':
    selections=[json.loads(l) for l in (a.output/'tag-control-trace.jsonl').read_bytes().splitlines()];p.need(any(r['kind']=='push_include' and r['attributes'].get('tag')=='VK_KHR_external_memory_capabilities-properties' and any('HOST CONTROL MUTANT' in x for x in r['selected_pieces']) for r in selections),'mutant not actually tag-selected')
   report['controls'][kind]={'source_line':592 if kind=='tag_changed' else None,'tag':'VK_KHR_external_memory_capabilities-properties' if kind=='tag_changed' else None,'authority':'EXPLICIT_HOST_SOURCE_OVERLAY_NOT_UNCHANGED_UPSTREAM','path':relative,'before_sha256':p.sha(before),'after_sha256':p.sha(target.read_bytes()) if target.exists() else None,'html_sha256':p.sha(output.read_bytes()) if output.exists() else None,'result':'EXPECTED_REJECTION' if kind=='active_missing' else 'UNCHANGED_INACTIVE_CORE_OUTPUT' if kind=='inactive_missing' else 'ACTUAL_TAG_CONTENT_CHANGED_OUTPUT'}
  micro=a.output/'condition-fixture';micro.mkdir();os.environ.pop('VULKAN_ADOC_TRACE',None);os.chdir(micro)
  (micro/'input.adoc').write_text('= HOST conditional control\n\nifdef::ACTIVE[]\ninclude::active.adoc[]\nendif::[]\nifndef::ACTIVE[]\ninclude::inactive.adoc[]\nendif::[]\n')
  (micro/'active.adoc').write_text('ACTIVE_SENTINEL\n');(micro/'inactive.adoc').write_text('INACTIVE_SENTINEL\n')
  for enabled in (True,False):
   output=micro/('on.html' if enabled else 'off.html');step('condition-'+str(enabled),[str(ruby),'--disable-gems',str(adoc),'--failure-level','ERROR','-a','ACTIVE' if enabled else 'ACTIVE!','-o',str(output),str(micro/'input.adoc')]);raw=output.read_bytes();p.need((b'ACTIVE_SENTINEL' in raw and b'INACTIVE_SENTINEL' not in raw) if enabled else b'INACTIVE_SENTINEL' in raw,'actual conditional branch control')
  report['controls']['condition_switch']={'authority':'SYNTHETIC_HOST_ENGINE_FIXTURE_NOT_UPSTREAM_CONFIG','on_sha256':p.sha((micro/'on.html').read_bytes()),'off_sha256':p.sha((micro/'off.html').read_bytes()),'result':'BRANCH_CONTENT_CHANGED'}
  report['observation']=h.analyze((a.output/'trace.jsonl').read_bytes(),a.output/'observed',*html,a.runtime_root)
  for label in ('baseline','observed'):
   root=a.output/label;actual={k:v for k,v in h.g.inventory(root).items() if not k.startswith('gen/')};p.need(actual=={n:p.sha(f['raw']) for n,f in files.items()},'source copy changed')
   for n,f in files.items():p.need((root/n).stat().st_mode&0o777==(0o755 if f['mode']=='100755' else 0o644),'source mode changed')
   for n,v in gen.items():p.need(p.sha((root/'gen'/n).read_bytes())==v,'generated input changed')
  p.need(h.runtime(a.runtime_root)==rt and h.generated(a.generated_root)==gen,'input cohort changed');p.need({str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned}==own,'implementation changed');p.need(p.git(ROOT,'rev-parse','HEAD').decode().strip()==report['tests_head'],'head changed')
  for path,digest in {**report['tools'],**report['linked_libraries'],**report['node_modules']}.items():p.need(p.sha(Path(path).read_bytes())==digest,'loaded tool/library changed')
  report['artifacts']={f.relative_to(a.output).as_posix():p.sha(f.read_bytes()) for f in a.output.iterdir() if f.is_file()};report['status']='FIXED_CORE_HTML_OBSERVED_MATCH'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  os.chdir(oldcwd);os.environ.clear();os.environ.update(oldenv);cancel.restore();(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'steps':len(report['steps'])}));return 0 if report['status']=='FIXED_CORE_HTML_OBSERVED_MATCH' else 2
if __name__=='__main__':raise SystemExit(main())
