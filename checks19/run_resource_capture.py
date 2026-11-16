"""Fixed source-cohort two-SSBO event capture; no arbitrary commands or GPU fault injection."""
import argparse,hashlib,json,math,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['checks19/run_resource_capture.py','checks19/process_supervisor19.py','tools/resource_capture19.py','tools/resource_contract_chain19.py','tools/binding_choice19.py','tools/upload_choice19.py','tools/memory_binding_contract19.py','tools/sync_contract19.py','tools/timeline_contract19.py','tools/descriptor_update_contract19.py','cases19/binding_choice/probe.c','cases19/binding_choice/compute.comp','cases19/binding_choice/normative.json','coverage/v1.0.19/pair.json']
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_json(p,lines=False):
 p=Path(p);need(p.is_file() and not p.is_symlink() and p.stat().st_size<=1024*1024,'bounded regular JSON file')
 def pairs(items):
  out={}
  for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
  return out
 def parse(raw):return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
 data=p.read_text()
 try:result=[parse(s) for s in data.splitlines()] if lines else parse(data)
 except RecursionError as e:raise ValueError('JSON nesting limit') from e
 # Bounded depth before interpreting any external object.
 def depth(v,n=0):
  need(n<=20,'JSON nesting limit')
  if type(v)is dict:
   for x in v.values():depth(x,n+1)
  elif type(v)is list:
   for x in v:depth(x,n+1)
 depth(result);return result
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True,timeout=30).strip()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ('toolchain','skill-root','output','spec-root'):ap.add_argument('--'+name,type=Path,required=True)
 for name in ('expected-tests-head','expected-skill-head'):ap.add_argument('--'+name,required=True)
 ap.add_argument('--obligations',type=Path);ap.add_argument('--expected-obligations-sha256');ap.add_argument('--development',action='store_true');ap.add_argument('--cancel-file',type=Path);ap.add_argument('--budget-seconds',type=float,default=120);ap.add_argument('--step-seconds',type=float,default=60);a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report=dict(status='BLOCKED',development=a.development,run_id=str(uuid.uuid4()),steps=[],runs=[],release_status='BLOCKED');cancel=None
 try:
  need(all(math.isfinite(v) and 0<v<=600 for v in (a.budget_seconds,a.step_seconds)),'finite execution budgets')
  identity=lambda:{name:dict(head=git(p,'rev-parse','HEAD'),dirty=git(p,'status','--porcelain')) for name,p in [('tests',ROOT),('skill',a.skill_root)]}
  before=identity();report['provenance']=before;need(before['tests']['head']==a.expected_tests_head and before['skill']['head']==a.expected_skill_head,'expected heads')
  need(a.development or all(not x['dirty'] for x in before.values()),'strict clean trees')
  pair=read_json(ROOT/'coverage/v1.0.19/pair.json');need(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','fixed pair')
  sources={p:sha(ROOT/p) for p in SOURCES}
  if not a.development:
   for p in SOURCES:need((ROOT/p).read_bytes()==subprocess.check_output(['git','-C',str(ROOT),'show',a.expected_tests_head+':'+p]),'source commit bytes')
  sys.path.insert(0,str(ROOT));from tools import resource_capture19 as rule,resource_contract_chain19 as chain,binding_choice19 as binding
  from checks19 import process_supervisor19 as sup
  config_hash=sha(a.toolchain);report['toolchain_sha256']=config_hash;t=read_json(a.toolchain);need(set(t)=={'tools','include','loader','icd','layer_path','library_path','validusage'} and all(type(v)is str for v in t.values()),'fixed toolchain keys')
  t={k:Path(v).resolve() for k,v in t.items()};icd=read_json(t['icd']);lib=Path(icd['ICD']['library_path']);lib=lib if lib.is_absolute() else t['library_path']/lib
  paths={'gcc':Path('/usr/bin/gcc'),'python':Path(sys.executable).resolve(),'loader':t['loader'],'icd':t['icd'],'icd_library':lib.resolve(),'layer_manifest':t['layer_path']/'VkLayer_khronos_validation.json','layer_library':t['library_path']/'libVkLayer_khronos_validation.so','ldd':Path('/usr/bin/ldd')}
  paths.update({k:t['tools']/k for k in ('glslangValidator','spirv-val','spirv-dis')})
  tools={k:sha(v) for k,v in paths.items()};headers={str(p.relative_to(t['include'])):sha(p) for p in sorted(t['include'].rglob('*.h'))};need(headers,'headers')
  normative=read_json(ROOT/'cases19/binding_choice/normative.json');normhash={x['path']:sha(a.spec_root/x['path']) for x in normative['sources']};need(all(normhash[x['path']]==x['sha256'] for x in normative['sources']),'fixed normative sources')
  obligations={k:'UNRESOLVED' for k in rule.OBLIGATIONS}
  if a.obligations:
   need(sha(a.obligations)==a.expected_obligations_sha256,'external obligations digest');obligations=read_json(a.obligations);report['obligations_input_sha256']=a.expected_obligations_sha256
  need(type(obligations)is dict and set(obligations)==set(rule.OBLIGATIONS) and all(v in ('CALLER_DECLARED','UNRESOLVED') for v in obligations.values()),'declaration authorities')
  env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','VK_DRIVER_FILES':str(t['icd']),'VK_LAYER_PATH':str(t['layer_path']),'LD_LIBRARY_PATH':str(t['library_path']),'MESA_SHADER_CACHE_DISABLE':'true'}
  report['validusage_config']='Accepted for shared toolchain compatibility; not consumed as a 309 VUID proof in this capture run'
  report.update(source_sha256=sources,tool_sha256=tools,headers_sha256=headers,normative=normative,environment=env,obligations=obligations)
  cancel=sup.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.budget_seconds
  def run(label,args,expected=0):
   args=list(map(str,args));out=a.output/(label+'.stdout');err=a.output/(label+'.stderr')
   old=dict(os.environ);os.environ.clear();os.environ.update(env)
   try:step=sup.run_step(args,out,err,timeout=a.step_seconds,total_deadline=deadline,cancellation=cancel)
   finally:os.environ.clear();os.environ.update(old)
   step.update(label=label,argv=args,stdout_sha256=sha(out),stderr_sha256=sha(err));report['steps'].append(step)
   need(type(step['returncode'])is int and step['returncode']==expected and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'controlled step failed '+label)
   return out,err
  src=ROOT/'cases19/binding_choice';spv=a.output/'compute.spv';asm=a.output/'compute.spvasm';exe=a.output/'probe'
  run('shader-compile',[paths['glslangValidator'],'-V','--target-env','vulkan1.1',src/'compute.comp','-o',spv]);run('shader-val',[paths['spirv-val'],'--target-env','vulkan1.1',spv]);run('shader-dis',[paths['spirv-dis'],spv,'-o',asm]);run('compile',[paths['gcc'],'-std=c11','-Wall','-Wextra','-Werror','-I'+str(t['include']),src/'probe.c',t['loader'],'-o',exe])
  out,err=run('linked-libraries',[paths['ldd'],exe]);linked={}
  for line in out.read_text().splitlines():
   if '=>' in line:
    name,tail=line.split('=>',1);p=Path(tail.strip().split()[0]);
    if p.is_absolute() and p.is_file():linked[name.strip()]=dict(path=str(p.resolve()),sha256=sha(p))
  need('libvulkan.so.1' in linked and linked['libvulkan.so.1']['sha256']==tools['loader'],'actual linked loader');report['linked_libraries']=linked
  artifacts={p.name:sha(p) for p in (spv,asm,exe)}
  for label,path,wrong,capture in [('legacy-set','set',False,False),('legacy-push','push',False,False),('legacy-recovery','set',False,False),('capture-good','set',False,True),('capture-wrong','set',True,True)]:
   events=a.output/(label+'.events.jsonl');args=[exe,path,'wrong-output' if wrong else 'good',spv]+([events] if capture else [])
   out,err=run(label,args,6 if wrong else 0);need(err.read_bytes()==b'','unexpected diagnostics');records=read_json(out,True);base=binding.check(records,path,wrong)
   row=dict(label=label,verification=base)
   if capture:
    trace=rule.adapt(records,read_json(events,True),wrong,obligations);checked=chain.check(trace);need(checked['status'] in ('CONSISTENT_DECLARED_TRACE','OBLIGATIONS_NOT_ESTABLISHED'),'capture rejected '+str(checked));row['chain']=checked
    f=a.output/(label+'.trace.json');f.write_text(json.dumps(trace,indent=2)+'\n');artifacts[events.name]=sha(events);artifacts[f.name]=sha(f)
   report['runs'].append(row)
  need(report['runs'][0]['verification']==report['runs'][2]['verification'],'legacy baseline recovery')
  need(all(x['verification']['identity']==report['runs'][0]['verification']['identity'] for x in report['runs']),'same actual device identity')
  need(identity()==before and {p:sha(ROOT/p) for p in SOURCES}==sources,'source/provenance drift');need(sha(a.toolchain)==config_hash and {k:sha(v) for k,v in paths.items()}==tools,'tools/config changed');need({str(p.relative_to(t['include'])):sha(p) for p in sorted(t['include'].rglob('*.h'))}==headers,'headers drift');need(all(sha(a.spec_root/k)==v for k,v in normhash.items()),'normative drift')
  if a.obligations:need(sha(a.obligations)==a.expected_obligations_sha256,'declarations drift')
  need(all(sha(a.output/k)==v for k,v in artifacts.items()),'artifacts drift')
  for step in report['steps']:
   for stream in ('stdout','stderr'):need(sha(a.output/(step['label']+'.'+stream))==step[stream+'_sha256'],'log drift')
  report['contract_states']={r['label']:r['chain']['status'] for r in report['runs'] if 'chain' in r}
  report['artifacts']=artifacts;report['status']='DEVELOPMENT_CAPTURE_RECHECKED' if a.development else 'CAPTURE_RECHECKED';report['scope']='fixed two-SSBO source-cohort parser; memory bind/free and binding output gate, not generic lifecycle solver or seven-family replay'
 except (Exception,KeyboardInterrupt) as e:report['error']=type(e).__name__+': '+str(e)
 finally:
  if cancel:cancel.restore()
  (a.output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':report['status'],'contract_states':report.get('contract_states',{})}));return 0 if report['status']!='BLOCKED' else 2
if __name__=='__main__':sys.exit(main())
