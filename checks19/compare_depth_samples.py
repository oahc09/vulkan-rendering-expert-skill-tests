"""Fixed 1→4→1 depth-scene experiment; no arbitrary command or performance ranking."""
import argparse,hashlib,importlib.util,json,math,os,pathlib,shutil,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASE='cases19/depth_msaa_sample/'
OWN={'checks19/compare_depth_samples.py','tools/depth_variant19.py','tools/sample_decision19.py','tools/depth_msaa_sample19.py',CASE+'probe.c',CASE+'run.py'}
SOURCES=sorted(OWN|{'checks19/process_supervisor19.py','tools/msaa_sample19.py','tools/render_sample19.py','tools/dynamic_color19.py','coverage/v1.0.19/pair.json','docs/v1.0.19-original-plan.md'}|{CASE+n for n in ('main.vert','main.frag','post.frag','normative.json')})
SPEC='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
ORDER=(('baseline1',1),('candidate4',4),('recovery1',1))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def read(p):return json.loads(pathlib.Path(p).read_text(),object_pairs_hook=pairs)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=30)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sources(head,dev=False):
 result={}
 for rel in SOURCES:
  p=ROOT/rel;require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT),'source escape')
  for ancestor in p.parents:
   if ancestor==ROOT:break
   require(not ancestor.is_symlink(),'source ancestor symlink')
  if not(dev and rel in OWN):require(p.read_bytes()==git(ROOT,'show',head+':'+rel),'source commit mismatch '+rel)
  result[rel]=sha(p)
 return result
def inventory(root,*,exclude_index=False):
 require(not root.is_symlink(),'artifact root symlink')
 out={}
 for p in root.rglob('*'):
  require(not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),'artifact escape')
  if p.is_file() and not(exclude_index and p==root/'comparison-index.json'):out[str(p.relative_to(root))]=sha(p)
 return out
def raw_verify(scene,samples,t):
 inventory(scene)
 sys.path.insert(0,str(ROOT/'tools'))
 depth=load('depth_compare_rule',ROOT/'tools/depth_msaa_sample19.py');variant=load('depth_compare_variant',ROOT/'tools/depth_variant19.py');shared=load('depth_compare_shared',ROOT/'tools/render_sample19.py');color=load('depth_compare_color',ROOT/'tools/dynamic_color19.py')
 r=read(scene/'summary.json');require(r['status']=='BOUNDED_DEPTH_MSAA_SAMPLE_PASS' and type(r['samples']) is int and r['samples']==samples,'variant status');uuid.UUID(r['run_id']);require(set(r['cases'])=={'good','depth-format','wrong-output','depth-disabled'},'case set')
 for key,rel in {'source_sha256':CASE+'probe.c','runner_sha256':CASE+'run.py','rules_sha256':'tools/depth_msaa_sample19.py','variant_rules_sha256':'tools/depth_variant19.py','resolve_rules_sha256':'tools/msaa_sample19.py','shared_rules_sha256':'tools/render_sample19.py','attachment_rules_sha256':'tools/dynamic_color19.py','normative_sha256':CASE+'normative.json'}.items():require(r[key]==sha(ROOT/rel),'source digest '+key)
 require(r['binary_sha256']==sha(scene/'probe'),'probe digest')
 layerpath=pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json';layer=read(layerpath)['layer'];spec=read(t['validusage']);require(sha(t['validusage'])==SPEC and layer['api_version']=='1.4.309','pinned normative/layer')
 for key,path in {'loader_sha256':t['loader'],'icd_manifest_sha256':t['icd'],'layer_manifest_sha256':layerpath,'spec_sha256':t['validusage']}.items():require(r[key]==sha(path),'tool binding')
 norm=read(ROOT/CASE/'normative.json');entries={e['vuid']:e for rows in spec['validation']['vkCmdDraw'].values() for e in rows};require(norm['entry']==entries[depth.VUID] and norm['source_sha256']==SPEC and norm['version']==spec['version info']==r['spec_version'],'normative exact mapping')
 require(set(r['shaders'])=={'main.vert','main.frag','post.frag'},'shader set')
 for stage,s in r['shaders'].items():
  require(s['source_sha256']==sha(ROOT/CASE/stage) and s['binary_sha256']==sha(scene/(stage+'.spv')) and s['target_env']=='vulkan1.1','shader binding');require(set(s['tools'])=={'compile','validate','disassemble'},'shader tools set')
  for name,tool in s['tools'].items():
   require(type(tool['exit_code']) is int and tool['exit_code']==0 and tool['tool_sha256']==sha(pathlib.Path(t['tools'])/{'compile':'glslangValidator','validate':'spirv-val','disassemble':'spirv-dis'}[name]),'shader tool result')
   for stream in ('stdout','stderr'):require(tool[stream+'_sha256']==sha(scene/(stage+'-'+name+'.'+stream)),'shader log binding')
 asm=(scene/'main.frag-disassemble.stdout').read_text();require(all(x in asm for x in ('DepthReplacing','BuiltIn FragDepth','OpKill','PushConstant')),'bounded depth shader signature')
 return verify_records(scene,samples,r,layer)

def verify_records(scene,samples,r,layer):
 sys.path.insert(0,str(ROOT/'tools'))
 depth=load('depth_record_rule',ROOT/'tools/depth_msaa_sample19.py');variant=load('depth_record_variant',ROOT/'tools/depth_variant19.py');shared=load('depth_record_shared',ROOT/'tools/render_sample19.py');color=load('depth_record_color',ROOT/'tools/dynamic_color19.py')
 require(set(r['cases'])=={'good','depth-format','wrong-output','depth-disabled'},'case set')
 identities=[];receipts=[]
 for mode,c in r['cases'].items():
  for stream in ('stdout','stderr'):require(c[stream+'_sha256']==sha(scene/(mode+'.'+stream)),'case log binding')
  rows=[json.loads(x,object_pairs_hook=pairs) for x in (scene/(mode+'.stdout')).read_text().splitlines()];rec={x['kind']:x for x in rows};require(len(rows)==len(rec) and rec==c['records'],'actual records')
  i=rec['identity'];require(i['deviceType']==4 and type(i['apiVersion']) is int and i['apiVersion']>>29==0 and i['apiVersion']>=4206592 and i['layerSpec']==4210997 and i['layerImplementation']==int(layer['implementation_version']) and i['queueFlags']&1,'runtime identity');identities.append(i)
  require(shared.graphics(rec['pipeline'],rec['manifest'],rec['limits']) and color.admit(rec['manifest'])['status']=='CONFIG_WITHIN_SCOPE','post graphics')
  require(rec['sampler']==dict(kind='sampler',min=0,mag=0,mipmap=0,u=2,v=2,w=2,minLod=0,maxLod=0,unnormalized=0,compare=0,anisotropy=0),'sampler')
  require(rec['descriptor']==dict(kind='descriptor',binding=0,count=1,type=1,stages=16,layout=1,sourceOrdinal=0,outputOrdinal=1,distinctImages=True),'descriptor')
  require(variant.topology(samples,rec['resolve_contract'],rec['multi_format'],rec['resolve_capabilities']),'topology')
  admission=depth.admit(rec['depth_contract'],rec['depth_format'],rec['resolve_capabilities'],samples=samples);target=dict(status='REJECTED',vuids=[depth.VUID]) if mode=='depth-format' else dict(status='DEPTH_DISABLED_CONTROL' if mode=='depth-disabled' else 'WITHIN_SCOPE',vuids=[]);require(admission==target==c['admission'],'depth admission')
  require(rec['pipeline_depth_capability']['format']==rec['depth_contract']['pipelineFormat'] and rec['pipeline_depth_capability']['optimalFeatures']&512,'depth support')
  require(rec['depth_transition']==dict(kind='depth_transition',oldLayout=0,newLayout=3,srcAccess=0,dstAccess=1536,srcStage=1,dstStage=768,aspect=2,baseMip=0,levels=1,baseLayer=0,layers=1),'depth dependency')
  expected=['depth-format '+depth.VUID] if mode=='depth-format' else [];rc=6 if mode=='wrong-output' else 4 if mode=='depth-disabled' else 0
  require((scene/(mode+'.stderr')).read_text().splitlines()==expected==c['diagnostics'] and type(c['exit_code']) is int and c['exit_code']==rc and rec['final']==dict(kind='final',errors=len(expected),rc=rc),'mode result')
  if mode=='depth-format':require(rec['execution']==dict(kind='execution',submitted=False,discarded=True),'invalid work submitted')
  else:
   require(rec['draw_sequence']==dict(kind='draw_sequence',modes=[0,1],nearDepth=.25,farDepth=.75,drawCount=2),'draw order')
   require(rec['source_contract']==dict(kind='source_contract',storeOp=0,loadOp=1,oldLayout=1,newLayout=1,srcStage=1024,dstStage=128,imageIsSource=True,aspect=1,baseMip=0,levelCount=1,baseLayer=0,layerCount=1,distinctPipelines=True,sourceViewFormat=37,viewType=1) and shared.admit(rec['two_pass'])['status']=='WITHIN_SCOPE','sampling dependency')
   ex=rec['execution'];require(ex['submitted'] is True and ex['fenceCompleted'] is True and ex['pixels']==depth.reference(mode!='depth-disabled'),'independent pixels')
  keys=['image_allocation','source_allocation','depth_allocation','buffer_allocation']+(['multi_allocation'] if samples==4 else [])
  require(all(type(rec[k]['selectedType']) is int and 0<=rec[k]['selectedType']<32 and rec[k]['memoryTypeBits']&(1<<rec[k]['selectedType']) for k in keys) and rec['buffer_allocation']['selectedFlags']&6==6,'memory choice')
  receipt=variant.allocations(samples,rec);require(receipt==c['allocation_receipt'],'allocation receipts');receipts.append(receipt)
 require(all(x==identities[0] for x in identities) and all(x==receipts[0] for x in receipts),'mode cohort')
 expected_workload=dict(width=4,height=4,draw_order=['near-partial','far-full'],near_depth=.25,far_depth=.75,source_fragment_sha256=sha(ROOT/CASE/'main.frag'),post_fragment_sha256=sha(ROOT/CASE/'post.frag'),vertex_sha256=sha(ROOT/CASE/'main.vert'),final_reference=depth.reference(),comparison_scope='Fixed endpoint pixels only, not general AA quality equivalence')
 require(r['workload']==expected_workload and r['validation_settings']=={'synchronization_validation':True,'shader_accesses_heuristic':True},'workload/settings')
 return dict(run_id=r['run_id'],samples=samples,identity=identities[0],workload=r['workload'],receipt=receipts[0],facts=dict(samples=samples,requested_bytes=receipts[0]['total_requested_bytes'],endpoint_error=0),summary_sha256=sha(scene/'summary.json'),artifacts=inventory(scene))
def main():
 p=argparse.ArgumentParser();p.add_argument('--expected-tests-head',required=True);p.add_argument('--expected-skill-head',required=True);p.add_argument('--skill-root',type=pathlib.Path,required=True);p.add_argument('--toolchain',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--required-samples',type=int,choices=(1,4),default=1);p.add_argument('--requested-bytes-budget',type=int,required=True);p.add_argument('--require-edge-quality',action='store_true');p.add_argument('--require-performance-gain',action='store_true');p.add_argument('--total-budget',type=float,default=300);p.add_argument('--step-timeout',type=float,default=90);p.add_argument('--cancel-file',type=pathlib.Path);p.add_argument('--development',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve();r=dict(status='BLOCKED',run_id=str(uuid.uuid4()),development=a.development,steps=[],variants=[],pending=[x[0] for x in ORDER]);cancel=None
 try:
  require(all(math.isfinite(x) and 0<x<=3600 for x in (a.total_budget,a.step_timeout)) and 0<=a.requested_bytes_budget<=2**63-1,'budget')
  head=git(ROOT,'rev-parse','HEAD').decode().strip();skill=git(a.skill_root,'rev-parse','HEAD').decode().strip();require(head==a.expected_tests_head and skill==a.expected_skill_head and all(len(x)==40 and set(x)<=set('0123456789abcdef') for x in (head,skill)),'expected heads');pair=read(ROOT/'coverage/v1.0.19/pair.json');require(pair['skill_sha']==skill and pair['release_status']=='BLOCKED' and pair['plan_sha256']==sha(ROOT/'docs/v1.0.19-original-plan.md') and 'version: 1.0.19' in (a.skill_root/'SKILL.md').read_text(),'pair');require(not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'Skill dirty');before=sources(head,a.development);r.update(tests_head=head,skill_head=skill,source_manifest=before)
  t=read(a.toolchain);require(set(t)=={'tools','include','loader','icd','layer_path','library_path','validusage'},'toolchain keys')
  for k,v in t.items():require(isinstance(v,str) and pathlib.Path(v).is_absolute() and pathlib.Path(v).exists(),'toolchain path')
  gcc=shutil.which('gcc');require(gcc,'gcc missing');paths=[pathlib.Path(gcc),pathlib.Path(sys.executable),pathlib.Path(t['loader']),pathlib.Path(t['icd']),pathlib.Path(t['validusage']),pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json']+[pathlib.Path(t['tools'])/n for n in ('glslangValidator','spirv-val','spirv-dis')]+list((pathlib.Path(t['include'])/'vulkan').glob('*.h'));toolhash={str(x):sha(x) for x in paths};configsha=sha(a.toolchain);r.update(toolchain_sha256=configsha,tool_hashes=toolhash,tool_scope='Explicit compiler/interpreter/tools/headers/loader/manifests, not complete transitive runtime attestation')
  supervisor=load('comparison_supervisor',ROOT/'checks19/process_supervisor19.py');decision=load('sample_decision',ROOT/'tools/sample_decision19.py');cancel=supervisor.Cancellation(a.cancel_file);cancel.install();deadline=time.monotonic()+a.total_budget;os.environ.update(VK_DRIVER_FILES=t['icd'],VK_LAYER_PATH=t['layer_path'],LD_LIBRARY_PATH=t['library_path'],MESA_SHADER_CACHE_DISABLE='true')
  for label,samples in ORDER:
   cancel.check(deadline);argv=[sys.executable,'-O',str(ROOT/CASE/'run.py'),'--samples',str(samples),'--tools',t['tools'],'--include',t['include'],'--loader',t['loader'],'--validusage',t['validusage'],'--output',str(a.output/label)];step=dict(label=label,samples=samples,argv=argv,started_monotonic=time.monotonic());r['steps'].append(step)
   try:step.update(supervisor.run_step(argv,a.output/(label+'.stdout'),a.output/(label+'.stderr'),timeout=a.step_timeout,total_deadline=deadline,cancellation=cancel))
   finally:
    step['ended_monotonic']=time.monotonic()
    for stream in ('stdout','stderr'):
     path=a.output/(label+'.'+stream)
     if path.is_file():step[stream+'_sha256']=sha(path)
   require(type(step['returncode']) is int and step['returncode']==0 and all(step[k] is False for k in ('timed_out','cancelled','budget_exhausted','unexpected_descendants')) and step['group_cleanup']['group_gone'] is True,'execution incomplete')
   verified=raw_verify(a.output/label,samples,t);verified['label']=label;r['variants'].append(verified);r['pending'].remove(label)
  require([x['label'] for x in r['variants']]==[x[0] for x in ORDER] and not r['pending'],'incomplete sequence');require(len({x['run_id'] for x in r['variants']})==3,'duplicate run');require(all(x['identity']==r['variants'][0]['identity'] and x['workload']==r['variants'][0]['workload'] for x in r['variants']),'cohort/workload mismatch');require(r['variants'][0]['facts']==r['variants'][2]['facts'] and r['variants'][0]['receipt']==r['variants'][2]['receipt'],'baseline recovery differs')
  policy=dict(required_samples=a.required_samples,requested_bytes_budget=a.requested_bytes_budget,require_edge_quality=a.require_edge_quality,require_performance_gain=a.require_performance_gain);r['policy']=policy;r['decision']=decision.decide(r['variants'][0]['facts'],r['variants'][1]['facts'],policy)
  cancel.check(deadline);require(before==sources(head,a.development) and head==git(ROOT,'rev-parse','HEAD').decode().strip() and skill==git(a.skill_root,'rev-parse','HEAD').decode().strip() and not git(a.skill_root,'status','--porcelain','--untracked-files=no'),'source changed');require(toolhash=={str(x):sha(x) for x in paths} and configsha==sha(a.toolchain),'tools changed')
  for saved in r['variants']:
   current=raw_verify(a.output/saved['label'],saved['samples'],t);current['label']=saved['label'];require(current==saved,'raw evidence changed')
  for step in r['steps']:
   for stream in ('stdout','stderr'):require(step[stream+'_sha256']==sha(a.output/(step['label']+'.'+stream)),'step logs changed')
  r['status']='DEVELOPMENT_COMPARISON_VERIFIED' if a.development else 'BOUNDED_COMPARISON_VERIFIED';r['limitations']=['Fixed 1→4→1 CPU ICD scene, not hardware performance/thermal measurement.','Allocation requests are not resident memory or heap pressure; driver-internal allocations excluded.','Zero endpoint error only for this full-coverage fixed scene, not general antialiasing equivalence.','Timing fields describe process supervision only, never GPU ranking.','Full v1.0.19 release remains BLOCKED.']
 except BaseException as error:r['error']=str(error);r['status']='CANCELLED' if cancel and cancel.requested() else 'BLOCKED'
 finally:
  if cancel:cancel.restore()
  try:r['artifacts']=inventory(a.output,exclude_index=True)
  except Exception as error:r['status']='BLOCKED';r['inventory_error']=str(error)
  (a.output/'comparison-index.json').write_text(json.dumps(r,indent=2)+'\n')
 print(r['status']);return 0 if r['status'].endswith('_VERIFIED') else 1
if __name__=='__main__':sys.exit(main())
