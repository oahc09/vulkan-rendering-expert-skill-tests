"""Fixed four-family resource suite. User JSON cannot select commands or code."""
import argparse,hashlib,importlib.util,json,math,os,pathlib,shutil,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
FAMILIES=('device_address','ray_query','robust_buffer','headless_wsi')
NEW={'checks19/run_resource_suite.py','checks19/resource_suite19.py'}
SOURCES=sorted(NEW|{'checks19/process_supervisor19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md'}|{'tools/'+x+'19.py' for x in FAMILIES}|{f'cases19/{x}/{f}' for x in FAMILIES for f in ('probe.c','run.py','normative.json')}|{f'cases19/{x}/compute.comp' for x in FAMILIES if x!='headless_wsi'}|{'cases19/device_address/capability_inventory.c'})
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(x,m):
 if not x:raise ValueError(m)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def source_manifest(head,development=False):
 result={}
 for rel in SOURCES:
  path=ROOT/rel;require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),'source escape '+rel)
  for parent in path.parents:
   if parent==ROOT:break
   require(not parent.is_symlink(),'source ancestor symlink')
  data=path.read_bytes()
  if not(development and rel in NEW):require(data==git(ROOT,'show',head+':'+rel),'source commit mismatch '+rel)
  result[rel]=sha(path)
 return result
def config(path):
 t=json.loads(path.read_text());require(set(t)=={'tools','include','loader','icd','layer_path','library_path','validusage'},'toolchain exact keys')
 for k,v in t.items():require(isinstance(v,str) and pathlib.Path(v).is_absolute() and pathlib.Path(v).exists(),'invalid tool path '+k)
 for n in ('glslangValidator','spirv-val','spirv-dis'):require(os.access(pathlib.Path(t['tools'])/n,os.X_OK),'tool executable')
 return t
def inventory(root):
 require(not root.is_symlink(),'output symlink');out={}
 for p in root.rglob('*'):
  require(not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),'artifact escape')
  if p.is_file() and p.name!='resource-index.json':out[str(p.relative_to(root))]=sha(p)
 return out
def require_complete(report):
 require(report['pending']==[],'pending families');require([s['label'] for s in report['steps']]==list(FAMILIES),'missing/extra execution step');require([s['family'] for s in report['families']]==list(FAMILIES),'missing/extra verified family');require(len({s['run_id'] for s in report['families']})==4,'child UUID reused')
 require(all(x['cpu_identity']==report['families'][0]['cpu_identity'] for x in report['families']),'CPU/tool cohort identities differ (not shared logical devices)')
 for step in report['steps']:
  require(type(step['returncode']) is int and step['returncode']==0 and not any(step[k] for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone'] is True,'unclean family execution')
def finalize_summary(report,output):
 def incomplete():
  (output/'SUMMARY.md').write_text('# 未完成 / Incomplete resource suite\n\nStatus: '+report['status']+'\nVerified families: '+', '.join(x['family'] for x in report['families'])+'\nPending: '+', '.join(report['pending'])+'\nNo total success or release acceptance. See resource-index.json.\n')
 try:inventory(output)
 except Exception as error:report['status']='BLOCKED';report['inventory_error']=str(error)
 if report['status'].endswith('_VERIFIED'):
  (output/'SUMMARY.md').write_text('# 资源链联合交付 / Bounded resource suite\n\n- BDA: pointer-table→64-word transform + guards; no stale/OOB pointer.\n- Ray query: BLAS→TLAS→two compute rays; no RT pipeline/SBT.\n- Robustness2: protected SSBO/NULL oracle; no unprotected OOB execution.\n- Headless WSI: two-generation clear/readback/present-fence retirement; no physical display or real resize.\n\n四条独立CPU场景均重新运行并复核正负控。Each has its own run UUID; no cross-family causal proof.\nVideo/special extensions remain unavailable. Full v1.0.19 release remains BLOCKED.\n')
 else:incomplete()
 try:report['artifacts']=inventory(output)
 except Exception as error:
  report['status']='BLOCKED';report['inventory_error']=str(error);report.pop('artifacts',None);incomplete()
def main():
 p=argparse.ArgumentParser();p.add_argument('--expected-tests-head',required=True);p.add_argument('--expected-skill-head',required=True);p.add_argument('--skill-root',type=pathlib.Path,required=True);p.add_argument('--toolchain',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--total-budget',type=float,default=300);p.add_argument('--step-timeout',type=float,default=90);p.add_argument('--cancel-file',type=pathlib.Path);p.add_argument('--development',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();report={'status':'BLOCKED','run_id':str(uuid.uuid4()),'development':a.development,'steps':[],'families':[],'pending':list(FAMILIES)};cancel=None
 try:
  require(all(math.isfinite(v) and 0<v<=3600 for v in (a.total_budget,a.step_timeout)),'finite positive budgets');head=git(ROOT,'rev-parse','HEAD').decode().strip();skill=git(a.skill_root,'rev-parse','HEAD').decode().strip();require(head==a.expected_tests_head and skill==a.expected_skill_head and all(len(v)==40 and all(c in '0123456789abcdef' for c in v) for v in (head,skill)),'explicit head mismatch');pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());require(pair['skill_sha']==skill and pair['release_status']=='BLOCKED' and pair['plan_sha256']==sha(ROOT/'docs/v1.0.19-original-plan.md') and 'version: 1.0.19' in (a.skill_root/'SKILL.md').read_text(),'pair/version mismatch');require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill dirty');before=source_manifest(head,a.development);report.update(tests_head=head,skill_head=skill,source_manifest=before)
  t=config(a.toolchain);gcc=shutil.which('gcc');require(gcc is not None,'gcc missing');paths=[pathlib.Path(gcc),pathlib.Path(sys.executable),pathlib.Path(t['loader']),pathlib.Path(t['icd']),pathlib.Path(t['validusage']),pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json']+[pathlib.Path(t['tools'])/n for n in ('glslangValidator','spirv-val','spirv-dis')]+list((pathlib.Path(t['include'])/'vulkan').glob('*.h'));toolhash={str(x):sha(x) for x in paths};configsha=sha(a.toolchain);report['toolchain_sha256']=configsha;report['tool_hashes']=toolhash;report['tool_scope']='Explicit compiler, interpreter, shader tools, headers, loader and ICD/layer manifests, not all transitive shared libraries.'
  supervisor=load('resource_supervisor',ROOT/'checks19/process_supervisor19.py');verifier=load('resource_verifier',ROOT/'checks19/resource_suite19.py');cancel=supervisor.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.total_budget;os.environ.update(VK_DRIVER_FILES=t['icd'],VK_LAYER_PATH=t['layer_path'],LD_LIBRARY_PATH=t['library_path'],MESA_SHADER_CACHE_DISABLE='true')
  for family in FAMILIES:
   cancel.check(deadline);argv=[sys.executable,'-O',str(ROOT/'cases19'/family/'run.py'),'--include',t['include'],'--loader',t['loader'],'--validusage',t['validusage'],'--output',str(a.output/family)]
   if family!='headless_wsi':argv+=['--tools',t['tools']]
   step={'label':family,'argv':argv,'started_monotonic':time.monotonic()};report['steps'].append(step)
   try:step.update(supervisor.run_step(argv,a.output/(family+'.stdout'),a.output/(family+'.stderr'),timeout=a.step_timeout,total_deadline=deadline,cancellation=cancel))
   finally:
    step['ended_monotonic']=time.monotonic()
    for stream in ('stdout','stderr'):
     path=a.output/(family+'.'+stream)
     if path.is_file():step[stream+'_sha256']=sha(path)
   require(step['returncode']==0 and not any(step.get(k) for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone'],'family execution incomplete');verified=verifier.verify_family(family,a.output/family,t);report['families'].append(verified);report['pending'].remove(family)
  cancel.check(deadline);require_complete(report);require(before==source_manifest(head,a.development) and head==git(ROOT,'rev-parse','HEAD').decode().strip() and skill==git(a.skill_root,'rev-parse','HEAD').decode().strip() and not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'sources changed');require(toolhash=={str(x):sha(x) for x in paths} and configsha==sha(a.toolchain),'tool cohort changed')
  for saved in report['families']:require(saved==verifier.verify_family(saved['family'],a.output/saved['family'],t),'family evidence changed')
  for st in report['steps']:
   for stream in ('stdout','stderr'):require(st[stream+'_sha256']==sha(a.output/(st['label']+'.'+stream)),'execution log changed')
  report['status']='DEVELOPMENT_RESOURCE_SUITE_VERIFIED' if a.development else 'BOUNDED_RESOURCE_SUITE_VERIFIED';report['scope']='Four independent authored CPU ICD runs. No shared resources, cross-family causality, hardware/display/performance or full release acceptance.'

 except BaseException as e:report['error']=str(e);report['status']='CANCELLED' if cancel and cancel.requested() else 'BLOCKED'
 finally:
  if cancel:cancel.restore()
  finalize_summary(report,a.output)
  (a.output/'resource-index.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status']);return 0 if report['status'].endswith('_VERIFIED') else 1
if __name__=='__main__':sys.exit(main())
