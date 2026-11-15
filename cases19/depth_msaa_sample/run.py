"""Real 4x MSAA color resolve to texture and fragment sampled channel reorder; CPU ICD only."""
import argparse,hashlib,json,os,pathlib,subprocess,uuid,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));import depth_msaa_sample19 as rules;import msaa_sample19 as resolve_rules;import render_sample19 as shared_rules;import dynamic_color19 as attachment_rules
SHA='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument('--tools',required=True);p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--validusage',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 require(sha(a.validusage)==SHA,'unpaired specification');spec=json.loads(pathlib.Path(a.validusage).read_text());entries={e['vuid']:e for group in spec['validation']['vkCmdDraw'].values() for e in group};norm=json.loads(pathlib.Path(__file__).with_name('normative.json').read_text());require(norm['source_sha256']==SHA and norm['entry']==entries[rules.VUID] and norm['version']==spec['version info'],'normative pairing')
 lm=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';layer=json.loads(lm.read_text())['layer'];require(layer['api_version']=='1.4.309','unpaired layer')
 source=pathlib.Path(__file__).with_name('probe.c');exe=a.output/'probe';r=subprocess.run(['gcc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+a.include,str(source),a.loader,'-o',str(exe)],capture_output=True,timeout=60)
 (a.output/'build.stdout').write_bytes(r.stdout);(a.output/'build.stderr').write_bytes(r.stderr);require(r.returncode==0,'compile failed')
 report={'run_id':str(uuid.uuid4()),'source_sha256':sha(source),'runner_sha256':sha(__file__),'rules_sha256':sha(rules.__file__),'attachment_rules_sha256':sha(attachment_rules.__file__),'shared_rules_sha256':sha(shared_rules.__file__),'resolve_rules_sha256':sha(resolve_rules.__file__),'binary_sha256':sha(exe),'loader_sha256':sha(a.loader),'icd_manifest_sha256':sha(os.environ['VK_DRIVER_FILES']),'layer_manifest_sha256':sha(lm),'spec_sha256':SHA,'spec_version':spec['version info'],'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'cases':{}}
 shaders={}
 for stage in ('main.vert','main.frag','post.frag'):
  src=source.with_name(stage);spv=a.output/(stage+'.spv');logs={}
  for name,cmd in [('compile',[str(pathlib.Path(a.tools)/'glslangValidator'),'-V','--target-env','vulkan1.1',str(src),'-o',str(spv)]),('validate',[str(pathlib.Path(a.tools)/'spirv-val'),'--target-env','vulkan1.1',str(spv)]),('disassemble',[str(pathlib.Path(a.tools)/'spirv-dis'),str(spv)])]:
   r=subprocess.run(cmd,capture_output=True,timeout=60);base=a.output/(stage+'-'+name);pathlib.Path(str(base)+'.stdout').write_bytes(r.stdout);pathlib.Path(str(base)+'.stderr').write_bytes(r.stderr);require(r.returncode==0,'shader tool failure');logs[name]={'exit_code':r.returncode,'stdout_sha256':sha(str(base)+'.stdout'),'stderr_sha256':sha(str(base)+'.stderr'),'tool_sha256':sha(cmd[0]),'version':subprocess.check_output([cmd[0],'--version'],text=True)}
  shaders[stage]={'source_sha256':sha(src),'binary_sha256':sha(spv),'target_env':'vulkan1.1','tools':logs}
 report['shaders']=shaders;report['normative_sha256']=sha(source.with_name('normative.json'))
 for mode in ('good','depth-format','wrong-output','depth-disabled'):
  actual=mode
  env=os.environ.copy();env['VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC']='true'
  r=subprocess.run([str(exe),actual,str(a.output/'main.vert.spv'),str(a.output/'main.frag.spv'),str(a.output/'post.frag.spv')],capture_output=True,timeout=30,env=env)
  (a.output/(mode+'.stdout')).write_bytes(r.stdout);(a.output/(mode+'.stderr')).write_bytes(r.stderr)
  expected_rc=6 if mode=='wrong-output' else 4 if mode=='depth-disabled' else 0
  require(r.returncode==expected_rc,'runtime exit');rows=[json.loads(x) for x in r.stdout.decode().splitlines()];rec={x['kind']:x for x in rows};require(len(rows)==len(rec),'duplicate records')
  i=rec['identity'];require(i['deviceType']==4 and i['apiVersion']>=4206592 and i['apiVersion']>>29==0 and i['layerSpec']==4210997 and i['layerImplementation']==int(layer['implementation_version']),'identity')
  require(shared_rules.graphics(rec['pipeline'],rec['manifest'],rec['limits']),'graphics config');require(rec['sampler']==dict(kind='sampler',min=0,mag=0,mipmap=0,u=2,v=2,w=2,minLod=0,maxLod=0,unnormalized=0,compare=0,anisotropy=0),'sampler config');require(rec['descriptor']==dict(kind='descriptor',binding=0,count=1,type=1,stages=16,layout=1,sourceOrdinal=0,outputOrdinal=1,distinctImages=True),'descriptor identity');attachment=attachment_rules.admit(rec['manifest']);require(attachment['status']=='CONFIG_WITHIN_SCOPE','attachment config')
  resolve_admission=resolve_rules.admit(rec['resolve_contract'],rec['multi_format'],rec['resolve_capabilities']);require(resolve_admission=={'status':'WITHIN_SCOPE','vuids':[]},'color resolve contract')
  require(rec['pipeline_depth_capability']['format']==rec['depth_contract']['pipelineFormat'] and rec['pipeline_depth_capability']['optimalFeatures']&512,'pipeline depth format support');require(rec['depth_transition']==dict(kind='depth_transition',oldLayout=0,newLayout=3,srcAccess=0,dstAccess=1536,srcStage=1,dstStage=768,aspect=2,baseMip=0,levels=1,baseLayer=0,layers=1),'depth dependency');
  admission=rules.admit(rec['depth_contract'],rec['depth_format'],rec['resolve_capabilities']);target={'status':'REJECTED','vuids':[rules.VUID]} if mode=='depth-format' else {'status':'DEPTH_DISABLED_CONTROL' if mode=='depth-disabled' else 'WITHIN_SCOPE','vuids':[]};require(admission==target,'depth rule pairing')
  if mode!='depth-format':
   require(rec['draw_sequence']==dict(kind='draw_sequence',modes=[0,1],nearDepth=.25,farDepth=.75,drawCount=2),'ordered draws')
   require(rec['source_contract']==dict(kind='source_contract',storeOp=0,loadOp=1,oldLayout=1,newLayout=1,srcStage=1024,dstStage=128,imageIsSource=True,aspect=1,baseMip=0,levelCount=1,baseLayer=0,layerCount=1,distinctPipelines=True,sourceViewFormat=37,viewType=1),'resolve write to sample dependency');require(shared_rules.admit(rec['two_pass'])['status']=='WITHIN_SCOPE','sampling chain')
  expected=['depth-format '+rules.VUID] if mode=='depth-format' else []
  require(r.stderr.decode().splitlines()==expected,'unexpected diagnostics');require(rec['final']=={'kind':'final','errors':len(expected),'rc':expected_rc},'cleanup/error count')
  ex=rec['execution']
  if mode=='depth-format':require(ex=={'kind':'execution','submitted':False,'discarded':True},'invalid work submitted')
  else:require(ex['submitted'] is True and ex['fenceCompleted'] is True and ex['pixels']==rules.reference(depth_enabled=mode!='depth-disabled'),'full independent output oracle')
  require(all(rec[k]['memoryTypeBits']&(1<<rec[k]['selectedType']) for k in ('image_allocation','source_allocation','multi_allocation','depth_allocation','buffer_allocation')) and rec['buffer_allocation']['selectedFlags']&6==6,'memory')
  report['cases'][mode]={'records':rec,'admission':admission,'diagnostics':expected,'exit_code':r.returncode,'stdout_sha256':sha(a.output/(mode+'.stdout')),'stderr_sha256':sha(a.output/(mode+'.stderr'))}
 report['status']='BOUNDED_DEPTH_MSAA_SAMPLE_PASS'
 report['limitations']=['Repository-authored controlled static depth scene, not external production bug.','CPU ICD only; D32 4x static LESS test/write, no bounds/stencil/depth resolve.','Two source draws: near partial then far full, resolved color sampled into final output.','Depth-disabled is legal rendering but fails intended occlusion oracle (exit4); wrong-output changes expectation only (exit6).','Depth-format negative aborts draw; no invalid submission.','Only final color read back; depth/sample planes not read back; no antialiasing quality/performance/full-domain claim.']
 report['validation_settings']={'synchronization_validation':True,'shader_accesses_heuristic':True}
 require(sha(resolve_rules.__file__)==report['resolve_rules_sha256'],'resolve rules changed');require(sha(shared_rules.__file__)==report['shared_rules_sha256'],'shared rules changed')
 require(sha(attachment_rules.__file__)==report['attachment_rules_sha256'] and all(sha(source.with_name(k))==v['source_sha256'] for k,v in shaders.items()),'dependency/shader changed');require(len({tuple(c['records']['identity'][k] for k in ('deviceID','vendorID','driverVersion','apiVersion','layerSpec','layerImplementation')) for c in report['cases'].values()})==1,'cohort identity changed');require(sha(source)==report['source_sha256'] and sha(__file__)==report['runner_sha256'] and sha(rules.__file__)==report['rules_sha256'],'source changed')
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
