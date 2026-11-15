"""Fresh unchanged Simulation Lab plus bounded quality decisions; no new solver."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN=['checks19/run_simulation_choice.py','tools/simulation_choice19.py','checks19/process_supervisor19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,s):
 if not c:raise ValueError(s)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30).decode().strip()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def snapshots(run):return [dict(scene=s,method=m,tick=t,state=json.loads((run/f'{s}-{m}-tick{t}.json').read_text()),constraints=json.loads((run/f'{s}-{m}-tick{t}-constraints.json').read_text())) for s in ('rope','cloth') for m in ('colored','jacobi') for t in range(1,9)]
def inventory(root):
 result={}
 for p in root.rglob('*'):
  require(not p.is_symlink() and p.resolve().is_relative_to(root),'artifact escape')
  if p.is_file() and p!=root/'report.json':result[str(p.relative_to(root))]=sha(p)
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('tools','include','loader','icd','libdir','layerdir','skill-root','output'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('expected-tests-head','expected-skill-head'):p.add_argument('--'+k,required=True)
 p.add_argument('--policy',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report=dict(status='BLOCKED',run_id=str(uuid.uuid4()),steps=[],scope='unchanged Simulation Lab; CPU numerical comparison, no complete independent trajectory or performance')
 try:
  def identity():return {k:dict(head=git(r,'rev-parse','HEAD'),dirty=git(r,'status','--porcelain')) for k,r in [('tests',ROOT),('skill',a.skill_root)]}
  before=identity();require(before=={'tests':{'head':a.expected_tests_head,'dirty':''},'skill':{'head':a.expected_skill_head,'dirty':''}},'exact clean pair required');pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());require(pair['skill_sha']==a.expected_skill_head and pair['release_status']=='BLOCKED','paired Skill');report['provenance']=before;report['pair']=pair
  lab=ROOT/'tests/fixtures/simulation_lab'
  rels=sorted(set(OWN+git(ROOT,'ls-files','tests/fixtures/simulation_lab','tests/fixtures/engine_scale_lab').splitlines()))
  sources={}
  for rel in rels:
   f=ROOT/rel;require(not f.is_symlink() and f.resolve().is_relative_to(ROOT),'source escape');raw=f.read_bytes();require(raw==subprocess.check_output(['git','-C',str(ROOT),'show',a.expected_tests_head+':'+rel]),'uncommitted source');sources[rel]=sha(f)
  report['sources']=sources
  rule=load('sim_choice',ROOT/'tools/simulation_choice19.py');supervisor=load('sim_supervisor',ROOT/'checks19/process_supervisor19.py')
  policy=json.loads(a.policy.read_text()) if a.policy else dict(baseline='colored',quality_targets=None,require_performance=False);policy_sha=sha(a.policy) if a.policy else None;report['policy']=policy;report['policy_sha256']=policy_sha
  paths=dict(cxx=Path('/usr/bin/g++'),build_python=Path('/usr/bin/python3').resolve(),shell=Path('/bin/sh').resolve(),ldd=Path('/usr/bin/ldd'),env=Path('/usr/bin/env'),python=Path(sys.executable).resolve(),loader=a.loader,icd=a.icd,icd_library=a.libdir/json.loads(a.icd.read_text())['ICD']['library_path'],layer_manifest=a.layerdir/'VkLayer_khronos_validation.json',layer_library=a.libdir/'libVkLayer_khronos_validation.so',glslang=a.tools/'glslangValidator',spirv_val=a.tools/'spirv-val')
  toolhash={k:sha(v) for k,v in paths.items()};headers={str(f.relative_to(a.include)):sha(f) for f in sorted((a.include/'vulkan').rglob('*.h'))};report['tools']=toolhash;report['headers']=headers
  env=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',LD_LIBRARY_PATH=str(a.libdir.resolve()),VK_DRIVER_FILES=str(a.icd.resolve()),VK_LAYER_PATH=str(a.layerdir.resolve()),MESA_SHADER_CACHE_DISABLE='true',VULKAN_SDK_PREFIX=str(a.include.parent.resolve()),GLSLANG=str(paths['glslang'].resolve()),SPIRV_VAL=str(paths['spirv_val'].resolve()),CXX='/usr/bin/g++');report['environment']=env
  cancel=supervisor.Cancellation();cancel.install();deadline=time.monotonic()+300
  def execute(label,args,timeout):
   argv=['/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],*map(str,args)];out=a.output/(label+'.stdout');err=a.output/(label+'.stderr');step=supervisor.run_step(argv,out,err,timeout=timeout,total_deadline=deadline,cancellation=cancel);step.update(label=label,argv=argv,stdout_sha256=sha(out),stderr_sha256=sha(err));report['steps'].append(step)
   require(type(step['returncode'])is int and step['returncode']==0 and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone']is True,'unclean '+label)
  try:
   execute('build',['/bin/sh',lab/'build.sh',a.output/'build'],90)
   # Resolve actual linked loader under the exact child environment, then hash.
   linked=subprocess.check_output(['/usr/bin/ldd',str(a.output/'build/simulation_lab')],env=env,text=True);(a.output/'linked-libraries.txt').write_text(linked);loader_lines=[l for l in linked.splitlines() if 'libvulkan.so.1 =>' in l];require(len(loader_lines)==1 and Path(loader_lines[0].split('=>')[1].split()[0]).resolve()==a.loader.resolve(),'actual loader differs')
   execute('run',[sys.executable,lab/'run_matrix.py',a.output/'build',a.output/'run','--skill-root',a.skill_root],190)
  finally:cancel.restore()
  raw_inventory=inventory(a.output)
  checker=load('original_sim_checker',lab/'verify_artifacts.py');report['original_verification']=checker.verify(a.output/'run',strict=True)
  build=json.loads((a.output/'build/build-manifest.json').read_text());require(all(sha(a.output/'build'/k)==v for k,v in build['artifacts'].items()),'actual build artifacts');report['build_artifacts']=build['artifacts']
  rows=snapshots(a.output/'run');report['quality_metrics']=rule.analyze(rows);report['decision']=rule.decide(rows,policy);require(report['decision']['status']!='UNKNOWN','invalid quality input/policy')
  # Controlled HOST corruption, never GPU fault injection or altered lab oracle.
  import copy
  corruptions={}
  for kind in ('missing_snapshot','duplicate_snapshot','missing_edge','duplicate_edge','stale_generation','residual_tamper','gpu_tamper'):
   changed=copy.deepcopy(rows)
   if kind=='missing_snapshot':changed.pop()
   elif kind=='duplicate_snapshot':changed[-1]=copy.deepcopy(changed[0])
   elif kind=='missing_edge':changed[0]['constraints']['edges'].pop()
   elif kind=='duplicate_edge':changed[0]['constraints']['edges'][-1]=changed[0]['constraints']['edges'][0][:]
   elif kind=='stale_generation':changed[0]['state']['normals'][0][3]=0
   elif kind=='residual_tamper':changed[0]['constraints']['edges'][0][4]+=1
   else:changed[0]['state']['gpu'][0][0]+=1
   try:rule.analyze(changed)
   except (ValueError,TypeError,KeyError):corruptions[kind]='REJECTED_HOST_CORRUPTION'
   else:raise ValueError('corruption accepted '+kind)
  require(set(corruptions)=={'missing_snapshot','duplicate_snapshot','missing_edge','duplicate_edge','stale_generation','residual_tamper','gpu_tamper'},'complete negative controls');report['negative_controls']=corruptions
  artifacts=inventory(a.output);require(artifacts==raw_inventory,'raw artifacts changed during verification');require(all(sha(ROOT/k)==v for k,v in sources.items()) and identity()==before,'source/pair changed');require({k:sha(v) for k,v in paths.items()}==toolhash and {str(f.relative_to(a.include)):sha(f) for f in sorted((a.include/'vulkan').rglob('*.h'))}==headers,'tool/header changed');require(a.policy is None or sha(a.policy)==policy_sha,'policy changed');require(inventory(a.output)==artifacts,'artifact changed');report['artifacts']=artifacts;report['status']='SIMULATION_LAB_QUALITY_VERIFIED_NOT_PERFORMANCE'
 except Exception as e:report['error']=type(e).__name__+': '+str(e)
 finally:(a.output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':report['status'],'decision':report.get('decision',{}).get('status')}));return 0 if report['status']!='BLOCKED' else 2
if __name__=='__main__':sys.exit(main())
