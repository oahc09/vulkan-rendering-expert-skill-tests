"""Fixed capability-admitted scene; never executes commands from toolchain JSON."""
import argparse,shutil,hashlib,importlib.util,json,os,pathlib,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES=['checks19/run_indirect_scene.py','checks19/process_supervisor19.py','tools/device_selection19.py','probes19/device_capabilities.c','tools/dynamic_color19.py','tools/dynamic_draw19.py','tools/indirect_draw19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md']+[str(p.relative_to(ROOT)) for p in (ROOT/'cases19/indirect_draw').iterdir() if p.suffix in ('.c','.py','.vert','.frag','.comp')]
NEW={'checks19/run_indirect_scene.py','tools/device_selection19.py','probes19/device_capabilities.c'}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(v,s):
 if not v:raise ValueError(s)
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],timeout=30)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sources(head,development):
 out={}
 for p in SOURCES:
  path=ROOT/p;require(path.is_file() and not path.is_symlink(),'source path');data=path.read_bytes()
  if not(development and p in NEW):require(data==git(ROOT,'show',head+':'+p),'source commit mismatch '+p)
  out[p]=sha(path)
 return out
def config(path):
 t=json.loads(path.read_text());keys={'tools','include','loader','icd','layer_path','library_path','validusage'};require(set(t)==keys,'toolchain keys must be exact path whitelist')
 for k,v in t.items():require(isinstance(v,str) and pathlib.Path(v).is_absolute() and pathlib.Path(v).exists(),'invalid tool path '+k)
 for name in ('glslangValidator','spirv-val','spirv-dis'):require(os.access(pathlib.Path(t['tools'])/name,os.X_OK),'tool not executable')
 return t
def raw_verify(scene,selection,toolchain=None):
 color=load('actual_color',ROOT/'tools/dynamic_color19.py');draw=load('actual_draw',ROOT/'tools/dynamic_draw19.py');indirect=load('actual_indirect',ROOT/'tools/indirect_draw19.py')
 r=json.loads((scene/'summary.json').read_text());layer=None
 if toolchain is not None:
  layer_path=pathlib.Path(toolchain['layer_path'])/'VkLayer_khronos_validation.json';layer=json.loads(layer_path.read_text())['layer'];version=list(map(int,layer['api_version'].split('.')));layer_spec=(version[0]<<22)|(version[1]<<12)|version[2]
  for key,path in {'loader_sha256':toolchain['loader'],'icd_manifest_sha256':toolchain['icd'],'layer_manifest_sha256':layer_path,'spec_sha256':toolchain['validusage']}.items():require(r[key]==sha(path),'tool cohort mismatch '+key)
  require(r['spec_version']==json.loads(pathlib.Path(toolchain['validusage']).read_text())['version info'],'spec version mismatch')
 require(r['status']=='BOUNDED_GPU_GENERATED_INDIRECT_PASS' and set(r['cases'])=={'good','offset','wrong-output','no-dispatch'},'scene schema')
 for name,c in r['cases'].items():
  for stream in ('stdout','stderr'):require(c[stream+'_sha256']==sha(scene/(name+'.'+stream)),'rawlog hash')
  rows=[json.loads(x) for x in (scene/(name+'.stdout')).read_text().splitlines()];actual={x['kind']:x for x in rows};require(len(rows)==len(actual) and actual==c['records'],'raw record mismatch');selection[0].match(selection[1],actual['identity']);
  if layer is not None:require(actual['identity']['layerSpec']==layer_spec and actual['identity']['layerImplementation']==int(layer['implementation_version']),'layer runtime mismatch')
  expected=['offset VUID-vkCmdDrawIndirect-offset-02710'] if name=='offset' else [];require((scene/(name+'.stderr')).read_text().splitlines()==expected==c['diagnostics'],'diagnostic mismatch');require(c['exit_code']==(6 if name=='wrong-output' else 4 if name=='no-dispatch' else 0),'exit oracle');require(actual['manifest']['enabled']==1 and actual['indirect']['multiDrawEnabled'] is False and actual['indirect']['firstInstanceEnabled'] is False,'enabled differs')
  require(color.admit(actual['manifest'])==c['attachment_admission'] and draw.admit(actual['pipeline'],actual['manifest'],actual['limits'])==c['admission'] and indirect.admit(actual['indirect'])==c['indirect_admission'],'recomputed rule mismatch');require(c['attachment_admission']['status']=='CONFIG_WITHIN_SCOPE' and c['admission']['status']=='DRAW_CONFIG_WITHIN_SCOPE' and c['indirect_admission']['status']==('REJECTED' if name=='offset' else 'ARG_LAYOUT_WITHIN_SCOPE') and c['indirect_admission']['vuids']==(['VUID-vkCmdDrawIndirect-offset-02710'] if name=='offset' else []),'rejected configuration cannot pass');require(actual['generation_dependency']=={'kind':'generation_dependency','srcAccess':64,'dstAccess':1,'srcStage':2048,'dstStage':2},'dependency mismatch');require(all(actual[k]['memoryTypeBits']&(1<<actual[k]['selectedType']) for k in ('image_allocation','buffer_allocation','indirect_allocation')) and all(actual[k]['selectedFlags']&6==6 for k in ('buffer_allocation','indirect_allocation')),'memory selection');require(actual['indirect_allocation']['initializedZeroBytes']==32,'initial argument state');require(actual['compute']['dispatched'] is (name!='no-dispatch'),'dispatch mismatch');require(all(actual['compute'][k]>=1 for k in ('maxInvocations','maxLocalX','maxGroupsX')),'compute limits');require(actual['final']=={'kind':'final','errors':len(expected),'rc':c['exit_code']},'final outcome');e=actual['execution']
  if name=='offset':require(e=={'kind':'execution','submitted':False,'discarded':True},'invalid submitted')
  else:
   expected_pixels=([[255,0,255,255]]*16 if name=='no-dispatch' else [[255,0,0,255] if (x+y)%2==0 else [0,0,255,255] for y in range(4) for x in range(4)]);require(e['submitted'] is True and e['fenceCompleted'] is True and e['pixels']==expected_pixels,'pixel oracle');require(actual['generated_args']['values']==([0,0,0,0] if name=='no-dispatch' else [3,1,0,0]),'args oracle');require(indirect.content(actual['generated_args']['values'],first_instance_enabled=actual['indirect']['firstInstanceEnabled'])['status']=='CONTENT_WITHIN_SCOPE','content admission')
 for stage in ('vert','frag','comp'):
  shader=r['shaders'][stage];require(shader['source_sha256']==sha(ROOT/'cases19/indirect_draw'/('main.'+stage)) and shader['binary_sha256']==sha(scene/(stage+'.spv')) and shader['target_env']=='vulkan1.1','shader binding')
  require(set(shader['tools'])=={'compile','validate','disassemble'},'missing shader tool facts')
  for name,tool in shader['tools'].items():
   if toolchain is not None:require(tool['tool_sha256']==sha(pathlib.Path(toolchain['tools'])/{'compile':'glslangValidator','validate':'spirv-val','disassemble':'spirv-dis'}[name]),'wrong tool identity')
   require(name in ('compile','validate','disassemble') and tool['exit_code']==0,'tool exit')
   for stream in ('stdout','stderr'):require(tool[stream+'_sha256']==sha(scene/(stage+'-'+name+'.'+stream)),'tool log changed')
 for key,path in {'source_sha256':'cases19/indirect_draw/probe.c','runner_sha256':'cases19/indirect_draw/run.py','rules_sha256':'tools/dynamic_draw19.py','indirect_rules_sha256':'tools/indirect_draw19.py','attachment_rules_sha256':'tools/dynamic_color19.py'}.items():require(r[key]==sha(ROOT/path),'source report binding')
 require(r['binary_sha256']==sha(scene/'probe'),'binary changed')
 return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--expected-tests-head',required=True);p.add_argument('--expected-skill-head',required=True);p.add_argument('--toolchain',type=pathlib.Path,required=True);p.add_argument('--skill-root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--profile',default='indirect-checker-v1');p.add_argument('--total-budget',type=float,default=240);p.add_argument('--cancel-file',type=pathlib.Path);p.add_argument('--development',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);report={'status':'BLOCKED','run_id':str(uuid.uuid4()),'development':a.development,'steps':[]};cancel=None
 try:
  head=git(ROOT,'rev-parse','HEAD').decode().strip();skillhead=git(a.skill_root,'rev-parse','HEAD').decode().strip();require(len(a.expected_tests_head)==40 and len(a.expected_skill_head)==40 and head==a.expected_tests_head and skillhead==a.expected_skill_head,'explicit expected pair mismatch');pair=json.loads((ROOT/'coverage/v1.0.19/pair.json').read_text());require(pair['release_status']=='BLOCKED' and 'version: 1.0.19' in (a.skill_root/'SKILL.md').read_text(),'candidate version/status mismatch');require(pair['skill_sha']==skillhead and pair['plan_sha256']==sha(ROOT/'docs/v1.0.19-original-plan.md'),'pair mismatch');require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill dirty');before=sources(head,a.development);report.update(tests_head=head,skill_head=skillhead,sources=before)
  t=config(a.toolchain);gcc=shutil.which('gcc');require(gcc is not None,'gcc missing');report['gcc']={'path':gcc,'sha256':sha(gcc),'version':subprocess.check_output([gcc,'--version'],text=True,timeout=10)};report['toolchain_sha256']=sha(a.toolchain);toolpaths=[pathlib.Path(t['tools'])/n for n in ('glslangValidator','spirv-val','spirv-dis')]+[pathlib.Path(t['loader']),pathlib.Path(t['icd']),pathlib.Path(t['validusage']),pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json'];toolpaths.append(pathlib.Path(gcc));toolpaths += list((pathlib.Path(t['include'])/'vulkan').glob('*.h'));toolhash={str(x):sha(x) for x in toolpaths};require(a.total_budget>0 and a.total_budget<=3600,'budget');deadline=time.monotonic()+a.total_budget
  supervisor=load('scene_supervisor',ROOT/'checks19/process_supervisor19.py');selection=load('scene_selection',ROOT/'tools/device_selection19.py');cancel=supervisor.Cancellation(a.cancel_file);cancel.install();os.environ.update(VK_DRIVER_FILES=t['icd'],VK_LAYER_PATH=t['layer_path'],LD_LIBRARY_PATH=t['library_path'],MESA_SHADER_CACHE_DISABLE='true')
  def step(label,argv):
   started=time.monotonic();result=supervisor.run_step(argv,a.output/(label+'.stdout'),a.output/(label+'.stderr'),timeout=min(180,a.total_budget),total_deadline=deadline,cancellation=cancel);report['steps'].append({'label':label,'argv':argv,'started_monotonic':started,'ended_monotonic':time.monotonic(),'stdout_sha256':sha(a.output/(label+'.stdout')),'stderr_sha256':sha(a.output/(label+'.stderr')),**result});require(result['returncode']==0 and not any(result.get(k) for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and result['group_cleanup']['group_gone'],'process did not complete cleanly')
  exe=a.output/'capabilities';step('compile',[gcc,'-Wall','-Wextra','-Werror','-I'+t['include'],str(ROOT/'probes19/device_capabilities.c'),t['loader'],'-o',str(exe)]);step('capabilities',[str(exe)]);caps=json.loads((a.output/'capabilities.stdout').read_text());admission=selection.select(caps,a.profile);report.update(capabilities=caps,admission=admission);require(admission['status']=='ADMITTED_SUPPORT_ONLY','capability/profile scope rejected')
  scene=a.output/'scene';step('scene',[sys.executable,'-O',str(ROOT/'cases19/indirect_draw/run.py'),'--tools',t['tools'],'--include',t['include'],'--loader',t['loader'],'--validusage',t['validusage'],'--output',str(scene)]);r=raw_verify(scene,(selection,admission),t);require(r['source_sha256']==before['cases19/indirect_draw/probe.c'] and r['runner_sha256']==before['cases19/indirect_draw/run.py'],'scene source mismatch')
  require(before==sources(head,a.development) and git(ROOT,'rev-parse','HEAD').decode().strip()==head and git(a.skill_root,'rev-parse','HEAD').decode().strip()==skillhead,'source changed');require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill changed during run');require(toolhash=={str(x):sha(x) for x in toolpaths},'tools changed');require(report['toolchain_sha256']==sha(a.toolchain),'toolchain configuration changed');
  for st in report['steps']:
   for stream in ('stdout','stderr'):require(st[stream+'_sha256']==sha(a.output/(st['label']+'.'+stream)),'execution logs changed')
  report['tool_hashes']=toolhash;report['tool_scope']='Explicit compiler tools, Vulkan headers, loader and ICD/layer manifests; transitive runtime shared libraries are not a complete environment attestation';report['scene_report_sha256']=sha(scene/'summary.json');report['status']='DEVELOPMENT_SCENE_VERIFIED' if a.development else 'BOUNDED_SCENE_VERIFIED';report['scope']='single CPU device; capability support != enable; authored fixture, not external project/full VK01/02'
  (a.output/'SUMMARY.md').write_text('# 有界场景验收 / Bounded scene acceptance\n\n真实 compute → indirect → graphics 及正负控通过。\nSingle CPU ICD, authored fixture. No hardware/performance/full-domain acceptance.\n')
 except BaseException as e:
  report['error']=str(e);report['status']='CANCELLED' if cancel and cancel.requested() else 'BLOCKED'
 finally:
  if cancel:cancel.restore()
  report['artifacts']={str(x.relative_to(a.output)):sha(x) for x in a.output.rglob('*') if x.is_file() and x.name!='scene-index.json'};(a.output/'scene-index.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status']);return 0 if report['status'].endswith('_VERIFIED') else 1
if __name__=='__main__':sys.exit(main())
