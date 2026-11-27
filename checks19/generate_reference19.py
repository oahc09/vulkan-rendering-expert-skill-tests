#!/usr/bin/env python3
"""Fixed official all-Vulkan368 VU plus two real reference pages. No user commands."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import reference_generation19 as h
from tools import asciidoc_execution19 as a
from checks19.process_supervisor19 import Cancellation,run_step
p=h.p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--docs-git',type=Path,required=True);parser.add_argument('--runtime-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--cancel-file',type=Path);args=parser.parse_args()
 for key in ('docs_git','runtime_root','output'):setattr(args,key,a.execution_path(getattr(args,key)))
 out=args.output;out.mkdir(parents=True,exist_ok=False);report={'status':'BLOCKED','steps':[],'scope':'VULKAN_1_4_ALL_REGISTERED_EXTENSIONS_NOT_SC; TWO_REFERENCE_HTML_PAGES','limitations':['not all reference HTML pages rendered','official Draft4 schema weak, Ruby json-schema not installed','fixed cohort agreement is not independent general normative semantic proof']}
 oldenv=dict(os.environ);oldcwd=Path.cwd();cancel=Cancellation(args.cancel_file);cancel.install();deadline=time.monotonic()+900
 owned=[Path(__file__).resolve(),ROOT/'tools/reference_generation19.py',ROOT/'tools/validusage_observer19.rb',ROOT/'tools/asciidoc_execution19.py',ROOT/'tools/prose_denominator19.py',ROOT/'tools/prose_generation19.py',ROOT/'checks19/process_supervisor19.py'];own={str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned};report['implementation']=own
 try:
  cancel.check(deadline);files=p.load(args.docs_git);runtime=a.runtime(args.runtime_root);report['tests_head']=p.git(ROOT,'rev-parse','HEAD').decode().strip();report['source_commit']=p.COMMIT;report['runtime_sha256']=a.RUNTIME_SHA
  rt=args.runtime_root;gem=rt/'usr/share/rubygems-integration/all/gems';ruby=rt/'usr/bin/ruby3.3';node=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node');adoc=gem/'asciidoctor-2.0.23/bin/asciidoctor';libs=out/'ruby-libs';libs.mkdir();(libs/'libruby-3.3.so.3.3').symlink_to(rt/'usr/lib/x86_64-linux-gnu/libruby-3.3.so.3.3')
  dep=Path('/usr/lib/python3/dist-packages');packages=['pyparsing','lxml','jsonschema','attrs','attr','referencing','rpds','jsonschema_specifications'];report['python_packages']={n:a.tree(dep/n) for n in packages}
  report['tools']={str(f):p.sha(f.read_bytes()) for f in (ruby,node,Path('/usr/bin/python3.13'),Path('/usr/bin/make'),Path('/usr/bin/git'),Path('/bin/sh'),Path('/usr/bin/ldd'))}
  env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(out),'LD_LIBRARY_PATH':str(libs),'RUBYLIB':':'.join(map(str,[rt/'usr/lib/ruby/3.3.0',rt/'usr/lib/x86_64-linux-gnu/ruby/3.3.0',gem/'asciidoctor-2.0.23/lib',gem/'rouge-4.5.1/lib'])),'NODE_PATH':str(rt/'usr/share/nodejs'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(dep)};os.environ.clear();os.environ.update(env)
  def step(label,argv,expected=0):
   r=run_step(argv,out/(label+'.stdout'),out/(label+'.stderr'),timeout=300,total_deadline=deadline,cancellation=cancel);r.update(label=label,argv=argv);report['steps'].append(r);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');p.need(r['returncode']==expected and not any(r[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and r['group_cleanup']['group_gone'],'step failed '+label)
  def command(root,observed=False):
   cmd=['/usr/bin/python3.13','-S','-B','makeSpec','-spec','all','-version','1.4','PYTHON=/usr/bin/python3.13 -S -B','ASCIIDOC='+str(ruby)+' --disable-gems '+str(adoc),'NODEJS='+str(node),'SPECDATE='+h.VERSION['date'],'SPECREMARK='+h.VERSION['comment'],'-j1']
   if observed:cmd+=['ADOCVUOPTS=-r '+str(root/'config/vu-to-json.rb')+' -r '+str(root/'config/quiet-include-failure.rb')+' -r '+str(ROOT/'tools/validusage_observer19.rb')+' -a vuprefix=vu- -a attribute-missing=skip']
   return cmd
  report['linked_libraries']={}
  for name,f in [('ruby',ruby),('node',node),('lxml',dep/'lxml/etree.cpython-313-x86_64-linux-gnu.so')]:
   step(name+'-ldd',['/usr/bin/ldd',str(f)])
   for line in (out/(name+'-ldd.stdout')).read_text().splitlines():
    for item in line.split():
     if item.startswith('/'):
      file=Path(item).resolve();report['linked_libraries'][str(file)]=p.sha(file.read_bytes())
  import_code="import json,sys,pyparsing,lxml.etree,jsonschema,attrs,referencing,rpds; print(json.dumps({n:getattr(m,'__file__',None) for n,m in sys.modules.items() if n.split('.')[0] in ('pyparsing','lxml','jsonschema','attrs','attr','referencing','rpds','jsonschema_specifications')}))"
  step('python-imports',['/usr/bin/python3.13','-S','-B','-c',import_code]);loaded=json.loads((out/'python-imports.stdout').read_bytes());report['python_loaded']={}
  for name,path in loaded.items():
   if path is None:continue
   f=Path(path).resolve();p.need(any(f.is_relative_to(dep/n) for n in packages),'unexpected actual Python module');report['python_loaded'][str(f)]=p.sha(f.read_bytes())
  p.need(any('lxml/etree.' in f for f in report['python_loaded']) and any('/jsonschema/' in f for f in report['python_loaded']),'missing actual dependency observation')
  results=[];report['runs']={} 
  for label in ('baseline','observed'):
   cancel.check(deadline);root=out/label;root.mkdir()
   for name,f in files.items():
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(f['raw']);dst.chmod(0o755 if f['mode']=='100755' else 0o644)
   os.chdir(root);step(label+'-generated',command(root)+['generated','refpages']);os.environ['VULKAN_VU_TRACE']=str(out/(label+'-vu-trace.jsonl'));step(label+'-validusage',command(root,label=='observed')+['validusage']);step(label+'-references',command(root)+[str(root/'gen/out/man/html'/(name+'.html')) for name in h.PAGES])
   raw=(root/'gen/out/validation/validusage.json').read_bytes();result=h.inspect_vu(raw,(root/'gen/xrefMap.py').read_bytes(),(root/'gen/pageMap.py').read_bytes(),(root/'gen/out/html/vkspec.html').read_bytes());gate=h.fixed_cohort(result);results.append(raw)
   schema_code="import json,jsonschema,sys; s=json.load(open(sys.argv[1]));v=json.load(open(sys.argv[2]));e=list(jsonschema.Draft4Validator(s).iter_errors(v));print(json.dumps({'validator':'Draft4','errors':[x.message for x in e],'const_keyword_ignored':True,'ruby_validation_claim':False}));sys.exit(bool(e))"
   step(label+'-schema',['/usr/bin/python3.13','-S','-B','-c',schema_code,str(root/'config/vu-to-json/vu_schema.json'),str(root/'gen/out/validation/validusage.json')])
   refs=[h.reference_page((root/'gen/out/man/html'/(name+'.html')).read_bytes(),name) for name in h.PAGES]
   ref_sources={f.name:p.sha(f.read_bytes()) for f in sorted((root/'gen/refpage').glob('*.adoc'))};p.need(len(ref_sources)==3553,'fixed reference-source matrix')
   report['runs'][label]={'gate':gate,'vuid_count':result['vuid_count'],'owners':result['owners'],'validusage_sha256':p.sha(raw),'references':refs,'ref_sources':ref_sources,'spec_attributes':(root/'gen/specattribs.adoc').read_text(),'generated_inventory':a.tree(root/'gen'),'full_output_inventory':a.tree(root)}
  report['vu_observation']=h.inspect_trace((out/'observed-vu-trace.jsonl').read_bytes(),out/'observed',rt)
  report['deterministic_validusage_sha256']=h.require_same(*results);p.need(report['runs']['baseline']['references']==report['runs']['observed']['references'],'reference HTML differed');p.need(report['runs']['baseline']['ref_sources']==report['runs']['observed']['ref_sources'],'reference sources differed')
  # Exact fixed overlays: quiet missing is not an upstream patch and never a pass.
  report['controls']={};root=out/'quiet-control';shutil.copytree(out/'baseline',root);os.chdir(root);target=root/'gen/validity/structs/VkMemoryDedicatedRequirements.adoc';before=target.read_bytes();target.unlink();vu=root/'gen/out/validation/validusage.json';vu.unlink();os.environ['VULKAN_VU_TRACE']=str(out/'quiet-control.jsonl');step('quiet-missing',command(root,True)+['validusage']);mutant=vu.read_bytes()
  rejected=False
  try:h.fixed_cohort(h.inspect_vu(mutant,(root/'gen/xrefMap.py').read_bytes(),(root/'gen/pageMap.py').read_bytes(),(root/'gen/out/html/vkspec.html').read_bytes()))
  except ValueError:rejected=True
  trace=[json.loads(line,object_pairs_hook=h.unique) for line in (out/'quiet-control.jsonl').read_bytes().splitlines()];p.need(rejected and any(r['kind']=='quiet_missing' and r['target']==str(target) for r in trace),'quiet omission not detected by strict audit');report['controls']['quiet_missing']={'authority':'EXPLICIT_OVERLAY','path':str(target.relative_to(root)),'before_sha256':p.sha(before),'after_sha256':None,'official_exit':0,'strict_rejected':True}
  root=out/'page-control';root.mkdir();src=out/'baseline';vid='VUID-vkBindBufferMemory-memory-01035';mapraw=(src/'gen/xrefMap.py').read_bytes();mapping=h.literal_map(mapraw,'xrefMap');mapping.pop(vid);(root/'xrefMap.py').write_text('xrefMap = '+repr(mapping)+'\n');shutil.copyfile(src/'gen/pageMap.py',root/'pageMap.py');(root/'validusage.json').write_bytes(results[0]);step('page-missing',['/usr/bin/python3.13','-S','-B',str(src/'scripts/add_validusage_pages.py'),'-xrefMap',str(root/'xrefMap.py'),'-pageMap',str(root/'pageMap.py'),'-validusage',str(root/'validusage.json')]);rejected=False
  try:h.inspect_vu((root/'validusage.json').read_bytes(),(root/'xrefMap.py').read_bytes(),(root/'pageMap.py').read_bytes(),(src/'gen/out/html/vkspec.html').read_bytes())
  except ValueError:rejected=True
  p.need(rejected and vid in (out/'page-missing.stdout').read_text(),'unmapped warning control');report['controls']['page_missing']={'authority':'EXPLICIT_OVERLAY','vuid':vid,'official_exit':0,'strict_rejected':True,'before_sha256':p.sha(mapraw),'after_sha256':p.sha((root/'xrefMap.py').read_bytes())}
  for label in ('baseline','observed'):
   root=out/label
   p.need(a.tree(root)==report['runs'][label]['full_output_inventory'],'completed output tree changed')
   for name,f in files.items():p.need((root/name).read_bytes()==f['raw'] and (root/name).stat().st_mode&0o777==(0o755 if f['mode']=='100755' else 0o644),'tracked source changed')
  p.need(a.runtime(rt)==runtime,'runtime changed')
  for n,v in report['python_packages'].items():p.need(a.tree(dep/n)==v,'Python dependency changed')
  for f,digest in {**report['tools'],**report['linked_libraries'],**report['python_loaded']}.items():p.need(p.sha(Path(f).read_bytes())==digest,'tool/library changed')
  p.need({str(f.relative_to(ROOT)):p.sha(f.read_bytes()) for f in owned}==own,'implementation changed');p.need(p.git(ROOT,'rev-parse','HEAD').decode().strip()==report['tests_head'],'head changed');p.need(p.load(args.docs_git)==files,'source Git changed')
  report['artifacts']={f.name:p.sha(f.read_bytes()) for f in out.iterdir() if f.is_file() and f.name!='report.json'};report['status']='FIXED_ALL_VU_AND_TWO_REFERENCE_PAGES_RECHECKED'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  os.chdir(oldcwd);os.environ.clear();os.environ.update(oldenv);cancel.restore();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'steps':len(report['steps'])}));return 0 if report['status']=='FIXED_ALL_VU_AND_TWO_REFERENCE_PAGES_RECHECKED' else 2
if __name__=='__main__':raise SystemExit(main())
