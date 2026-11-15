"""Strict fixed external-task replay: HOST class, software Vulkan bug, regressions."""
import argparse,hashlib,importlib,json,math,os,pathlib,re,subprocess,sys,time,uuid,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
TASKS=('fence_host','amber_gpu','related_gpu')
PLANNED={'historical_defects':2,'host_boundary_defects':1,'software_vulkan_defects':1,'ordinary_regression_cases':3,'ordinary_regression_executions':6,'blind_repairs':0,'physical_hardware_runs':0,'amber1119_executed':False}
SOURCES=['checks19/run_external_suite.py','tools/external_suite19.py','checks19/process_supervisor19.py','tools/external_fence19.py','checks19/run_external_fence_task.py','cases19/external_fence/harness.cpp','cases19/external_fence/stubs/common/helpers.h','cases19/external_fence/stubs/core/device.h','tools/external_amber95119.py','checks19/run_external_amber951.py','tools/external_related19.py','checks19/run_external_related.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30)
def unique(pairs):
 out={}
 for k,v in pairs:require(k not in out,'duplicate JSON key');out[k]=v
 return out
def source_state(tests_head,skill_head,skill_root):
 require(all(re.fullmatch('[0-9a-f]{40}',x or '') for x in (tests_head,skill_head)),'full expected heads required')
 for root,head in ((ROOT,tests_head),(skill_root,skill_head)):
  require(git(root,'rev-parse','HEAD').decode().strip()==head,'expected head mismatch')
  require(not git(root,'status','--porcelain'),'repository dirty (including untracked files)')
 hashes={}
 for rel in SOURCES:
  p=ROOT/rel;require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT),'source escape')
  for q in p.parents:
   if q==ROOT:break
   require(not q.is_symlink(),'source ancestor symlink')
  data=p.read_bytes();require(data==git(ROOT,'show',tests_head+':'+rel),'source commit mismatch');hashes[rel]=sha(p)
 pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text(),object_pairs_hook=unique)
 require(pair['skill_sha']==skill_head and pair['release_status']=='BLOCKED' and pair['plan_sha256']==sha(ROOT/'docs/v1.0.19-original-plan.md') and 'version: 1.0.19' in (skill_root/'SKILL.md').read_text(),'pair/version mismatch')
 return hashes

def config(path):
 d=json.loads(path.read_text(),object_pairs_hook=unique);require(set(d)=={'artifact_root','fence_repo','headers'},'fixed config keys')
 for k,v in d.items():require(isinstance(v,str) and pathlib.Path(v).is_absolute() and pathlib.Path(v).is_dir(),'invalid config directory');d[k]=str(pathlib.Path(v).resolve())
 return d

def inventory(root):
 result={}
 for p in root.rglob('*'):
  require(not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),'output escape')
  if p.is_file() and p not in (root/'external-index.json',root/'external-index.tmp'):result[p.relative_to(root).as_posix()]=sha(p)
 return result

def clean_step(s):
 require(type(s['returncode'])is int and s['returncode']==0,'child process failed')
 for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants'):require(s[k] is False,'child process incomplete')
 c=s['group_cleanup'];require(type(s['pid'])is int and s['pid']>0 and c['pgid']==s['pid'] and c['group_gone'] is True,'owned group not clean')
 require(type(c['term_sent'])is bool and type(c['kill_sent'])is bool and isinstance(c['reaped_descendants'],list) and all(type(x)is int and x>0 for x in c['reaped_descendants']),'cleanup fields')
 require(not c.get('ownership_lost') and not c.get('direct_child_unreaped'),'cleanup not established')

def complete(report):
 require(report['planned_counts']==PLANNED,'classification counts changed')
 require(report['pending']==[] and [x['label'] for x in report['steps']]==list(TASKS) and [x['task'] for x in report['verified']]==list(TASKS),'missing/reordered task')
 require(len({x['child_run_id'] for x in report['verified']})==3,'child run UUID reused')
 expected=[('ORIGINAL_CLASS_HOST_TEST_DOUBLE',1,False),('ORIGINAL_ENGINE_SOFTWARE_VULKAN_BUG',1,True),('ORIGINAL_NEIGHBOR_REGRESSIONS_NOT_NEW_BUGS',0,True)]
 for v,e in zip(report['verified'],expected):require((v['classification'],v['original_bugs'],v['gpu_executed'])==e,'task classification changed')
 for step in report['steps']:clean_step(step)

def write_index(output,report):
 tmp=output/'external-index.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,output/'external-index.json')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-tests-head',required=True);p.add_argument('--expected-skill-head',required=True);p.add_argument('--skill-root',type=pathlib.Path,required=True);p.add_argument('--config',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--total-budget',type=float,default=180);p.add_argument('--step-timeout',type=float,default=60);p.add_argument('--cancel-file',type=pathlib.Path);a=p.parse_args()
 require(not a.output.exists() and not a.output.is_symlink(),'fresh output required');a.output.mkdir(parents=True);a.output=a.output.resolve();a.skill_root=a.skill_root.resolve()
 report={'schema':1,'status':'BLOCKED','run_id':str(uuid.uuid4()),'release_status':'BLOCKED','planned_counts':PLANNED,'steps':[],'verified':[],'pending':list(TASKS),'scope':'Two historical defects: original class HOST boundary and original full Amber software Vulkan runtime. Three unchanged neighboring regression cases (six executions), not additional defects. Not blind repair/hardware/full release. Unsupported Amber depth-clamp candidate not executed and not counted.'};cancel=None;original_environment=None
 try:
  require(all(math.isfinite(x) and 0<x<=3600 for x in (a.total_budget,a.step_timeout)),'finite positive budgets')
  before=source_state(a.expected_tests_head,a.expected_skill_head,a.skill_root);cfg=config(a.config);cfgsha=sha(a.config)
  cfg.update(_expected_tests_head=a.expected_tests_head,_expected_skill_head=a.expected_skill_head,_expected_pair_sha256=sha(ROOT/'coverage/v1.0.19/pair.json'))
  report.update(tests_head=a.expected_tests_head,skill_head=a.expected_skill_head,source_manifest=before,config_sha256=cfgsha)
  # No helper import occurs until its exact committed bytes were checked.
  sys.path.insert(0,str(ROOT));v=importlib.import_module('tools.external_suite19');supervisor=importlib.import_module('checks19.process_supervisor19')
  v.a.verify_artifacts(pathlib.Path(cfg['artifact_root']));v.f.verify_parent(cfg['fence_repo'])
  for label in v.f.SOURCES:
   for name in v.f.SOURCES[label]:v.f.source_bytes(cfg['fence_repo'],label,name)
  headers=pathlib.Path(cfg['headers']);hh={x.relative_to(headers).as_posix():sha(x) for x in sorted(headers.rglob('*.h'))}
  require(hashlib.sha256(json.dumps(hh,sort_keys=True,separators=(',',':')).encode()).hexdigest()==v.f.HEADER_TREE_SHA256,'header cohort mismatch')
  execution_tools={str(pathlib.Path(x).resolve()):sha(pathlib.Path(x).resolve()) for x in (sys.executable,shutil.which('g++',path='/usr/bin:/bin'))};report['execution_tool_sha256']=execution_tools
  original_environment=dict(os.environ);os.environ.clear();os.environ.update(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',VULKAN_SKILL_ROOT=str(a.skill_root))
  cancel=supervisor.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.total_budget
  report['status']='IN_PROGRESS';write_index(a.output,report)
  for task in TASKS:
   cancel.check(deadline);child_id=str(uuid.uuid4());child=a.output/(task+'-'+child_id)
   if task=='fence_host':argv=[sys.executable,str(ROOT/'checks19/run_external_fence_task.py'),'--source-repo',cfg['fence_repo'],'--headers',cfg['headers'],'--out',str(child)]
   else:argv=[sys.executable,str(ROOT/('checks19/run_external_amber951.py' if task=='amber_gpu' else 'checks19/run_external_related.py')),'--artifact-root',cfg['artifact_root'],'--out',str(child)]
   argv+=['--run-id',child_id]
   step={'label':task,'child_run_id':child_id,'directory':child.name,'argv':argv,'started_monotonic':time.monotonic()};report['steps'].append(step);write_index(a.output,report)
   try:step.update(supervisor.run_step(argv,a.output/(task+'.stdout'),a.output/(task+'.stderr'),timeout=a.step_timeout,total_deadline=deadline,cancellation=cancel))
   finally:
    step['ended_monotonic']=time.monotonic()
    for stream in ('stdout','stderr'):
     q=a.output/(task+'.'+stream)
     if q.exists():step[stream+'_sha256']=sha(q)
   clean_step(step);checked=v.verify(task,child,cfg,child_id);checked.update(child_run_id=child_id,directory=child.name);report['verified'].append(checked);report['pending'].remove(task);write_index(a.output,report)
  cancel.check(deadline);complete(report)
  require(before==source_state(a.expected_tests_head,a.expected_skill_head,a.skill_root) and cfgsha==sha(a.config),'source/config changed')
  for saved in report['verified']:
   fresh=v.verify(saved['task'],a.output/saved['directory'],cfg,saved['child_run_id']);require(all(saved[k]==val for k,val in fresh.items()),'child evidence changed')
  for step in report['steps']:
   for stream in ('stdout','stderr'):require(step[stream+'_sha256']==sha(a.output/(step['label']+'.'+stream)),'root log changed')
  require(execution_tools=={p:sha(p) for p in execution_tools},'execution tool changed')
  cancel.check(deadline)
  report['status']='BOUNDED_EXTERNAL_TASK_SUITE_VERIFIED'
 except BaseException as e:report['status']='CANCELLED' if cancel and cancel.requested() else 'BLOCKED';report['error']=str(e);report['failed_or_interrupted_task']=report['pending'][0] if report['pending'] else 'final_verification'
 finally:
  if cancel:cancel.restore()
  if original_environment is not None:os.environ.clear();os.environ.update(original_environment)
  try:report['artifacts']=inventory(a.output)
  except Exception as e:report['status']='BLOCKED';report['inventory_error']=str(e)
  (a.output/'SUMMARY.md').write_text('# External tasks / 外部任务\n\nStatus: '+report['status']+'\n\nVerified: '+', '.join(x['task'] for x in report['verified'])+'\nPending: '+', '.join(report['pending'])+'\nFailure/interruption: '+str(report.get('failed_or_interrupted_task','none'))+'; '+str(report.get('error','none'))+'\n\nPlanned classification (not completed counts): '+json.dumps(PLANNED,sort_keys=True)+'\n\n'+report['scope']+'\n')
  try:report['artifacts']=inventory(a.output)
  except Exception:report['status']='BLOCKED';(a.output/'SUMMARY.md').write_text('BLOCKED: artifact inventory failed; no total success.\n')
  write_index(a.output,report)
 print(report['status']);return 0 if report['status']=='BOUNDED_EXTERNAL_TASK_SUITE_VERIFIED' else 1
if __name__=='__main__':sys.exit(main())
