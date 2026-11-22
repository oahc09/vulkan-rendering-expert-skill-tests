"""Real primary→secondary dynamic rendering graphics draw and full readback; CPU ICD only."""
import argparse,hashlib,json,os,pathlib,subprocess,uuid,sys,math
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));import secondary_draw19 as rules;import dynamic_draw19 as draw_rules;import dynamic_color19 as attachment_rules
SHA='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def validate_secondary_graphics(rec):
 """Common graphics facts, independent of primary attachment-format comparison."""
 p=rec['pipeline'];i=rec['inheritance'];limits=rec['limits']
 fixed={'colorCount':1,'samples':1,'viewMask':0,'vertexCount':3,'instanceCount':1,'blendEnable':0,'writeMask':15,'cullMode':0,'rasterizerDiscard':0,'stageCount':2,'stageMask':17,'topology':3,'depthStencilPresent':0,'firstVertex':0,'firstInstance':0,'attachmentFormat':37}
 require(all(type(p.get(k)) is int and p[k]==v for k,v in fixed.items()),'secondary fixed graphics fields')
 require(type(p.get('format')) is int and p['format']==i['colorFormat'] and p['samples']==i['samples'] and p['colorCount']==i['colorCount'] and p['viewMask']==i['viewMask'],'secondary pipeline/inheritance consistency')
 require(p.get('unusedAttachmentsEnabled') is False,'unused attachments disabled')
 for key in ('viewport','scissor'):
  require(isinstance(p.get(key),list) and len(p[key])==4 and all(type(v) in (int,float) and math.isfinite(v) for v in p[key]) and p[key]==[0,0,4,4],'secondary viewport/scissor')
 require(type(p.get('maxColorAttachments')) is int and p['maxColorAttachments']>=1,'color attachment limit')
 for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight','viewportBoundsMin','viewportBoundsMax'):require(type(limits.get(k)) in (int,float) and math.isfinite(limits[k]),'finite graphics limits')
 require(all(limits[k]>=4 for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight')) and limits['viewportBoundsMin']<=0 and limits['viewportBoundsMax']>=4,'graphics limits insufficient')
 return {'status':'SECONDARY_GRAPHICS_FIXED_FIELDS_VALID','scope':'Checks pipeline against secondary inheritance, not primary format validity or full shader reflection.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--tools',required=True);p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--validusage',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 require(sha(a.validusage)==SHA,'unpaired specification');spec=json.loads(pathlib.Path(a.validusage).read_text());entries={e['vuid']:e for name in ('vkCmdExecuteCommands','vkQueueSubmit') for group in spec['validation'][name].values() for e in group}
 lm=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';layer=json.loads(lm.read_text())['layer'];require(layer['api_version']=='1.4.309','unpaired layer')
 source=pathlib.Path(__file__).with_name('probe.c');exe=a.output/'probe';r=subprocess.run(['gcc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+a.include,str(source),a.loader,'-o',str(exe)],capture_output=True,timeout=60)
 (a.output/'build.stdout').write_bytes(r.stdout);(a.output/'build.stderr').write_bytes(r.stderr);require(r.returncode==0,'compile failed')
 report={'run_id':str(uuid.uuid4()),'source_sha256':sha(source),'runner_sha256':sha(__file__),'rules_sha256':sha(rules.__file__),'draw_rules_sha256':sha(draw_rules.__file__),'normative_sha256':sha(source.with_name('normative.json')),'attachment_rules_sha256':sha(attachment_rules.__file__),'binary_sha256':sha(exe),'loader_sha256':sha(a.loader),'icd_manifest_sha256':sha(os.environ['VK_DRIVER_FILES']),'layer_manifest_sha256':sha(lm),'spec_sha256':SHA,'spec_version':spec['version info'],'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'cases':{}}
 shaders={}
 for stage in ('vert','frag'):
  src=source.with_name('main.'+stage);spv=a.output/(stage+'.spv');logs={}
  for name,cmd in [('compile',[str(pathlib.Path(a.tools)/'glslangValidator'),'-V','--target-env','vulkan1.1',str(src),'-o',str(spv)]),('validate',[str(pathlib.Path(a.tools)/'spirv-val'),'--target-env','vulkan1.1',str(spv)]),('disassemble',[str(pathlib.Path(a.tools)/'spirv-dis'),str(spv)])]:
   r=subprocess.run(cmd,capture_output=True,timeout=60);base=a.output/(stage+'-'+name);pathlib.Path(str(base)+'.stdout').write_bytes(r.stdout);pathlib.Path(str(base)+'.stderr').write_bytes(r.stderr);require(r.returncode==0,'shader tool failure');logs[name]={'exit_code':r.returncode,'stdout_sha256':sha(str(base)+'.stdout'),'stderr_sha256':sha(str(base)+'.stderr'),'tool_sha256':sha(cmd[0]),'version':subprocess.check_output([cmd[0],'--version'],text=True)}
  shaders[stage]={'source_sha256':sha(src),'binary_sha256':sha(spv),'target_env':'vulkan1.1','tools':logs}
 report['shaders']=shaders;norm=json.loads(source.with_name('normative.json').read_text());require(norm['source_sha256']==SHA and norm['version']==spec['version info']['api version']=='1.4.309' and norm['entry']==entries[rules.VUID],'normative source pairing');require(norm['lifecycle_entry']==entries['VUID-vkQueueSubmit-pCommandBuffers-00070'],'lifecycle normative pairing')
 for mode in ('good','inheritance-format','wrong-output','lifecycle','lifecycle-wrong-output'):
  r=subprocess.run([str(exe),mode,str(a.output/'vert.spv'),str(a.output/'frag.spv')],capture_output=True,timeout=30);(a.output/(mode+'.stdout')).write_bytes(r.stdout);(a.output/(mode+'.stderr')).write_bytes(r.stderr);require(r.returncode==(6 if mode in ('wrong-output','lifecycle-wrong-output') else 0),'runtime failure')
  rows=[json.loads(x) for x in r.stdout.decode().splitlines()];rec={x['kind']:x for x in rows};require(len(rows)==len(rec),'duplicate records');i=rec['identity'];require(i['deviceType']==4 and i['apiVersion']>=4206592 and i['layerSpec']==4210997 and i['layerImplementation']==int(layer['implementation_version']),'runtime identity');attachment_admission=attachment_rules.admit(rec['manifest']);require(attachment_admission['status']=='CONFIG_WITHIN_SCOPE','base attachment admission');admission=rules.admit(rec['inheritance'],rec['execute_config'],rec['manifest'],rec['pipeline']);
  secondary_graphics=validate_secondary_graphics(rec)
  if mode!='inheritance-format':require(draw_rules.admit(rec['pipeline'],rec['manifest'],rec['limits'])['status']=='DRAW_CONFIG_WITHIN_SCOPE','graphics pipeline admission')
  expected=[rules.VUID] if mode=='inheritance-format' else [];require(admission=={'status':'REJECTED' if expected else 'SECONDARY_WITHIN_SCOPE','vuids':expected},'actual rule pairing');diagnostics=['stale-primary-submit VUID-vkQueueSubmit-pCommandBuffers-00070'] if mode.startswith('lifecycle') else ['execute-secondary '+x for x in expected];require(r.stderr.decode().splitlines()==diagnostics,'unexpected VVL');require(rec['final']=={'kind':'final','errors':len(diagnostics),'rc':6 if mode in ('wrong-output','lifecycle-wrong-output') else 0},'cleanup failure');ex=rec['execution']
  require(all(rec[k]['memoryTypeBits']&(1<<rec[k]['selectedType']) for k in ('image_allocation','buffer_allocation')) and rec['buffer_allocation']['selectedFlags']&6==6,'memory selection')
  if mode=='inheritance-format':require(ex=={'kind':'execution','submitted':False,'discarded':True},'invalid draw submitted')
  else:require(ex['submitted'] is True and ex['fenceCompleted'] is True and ex['pixels']==rules.reference(),'independent checker oracle')
  lifecycle_admission=rules.lifecycle(rec) if mode.startswith('lifecycle') else None
  if mode.startswith('lifecycle'):
   actual_order=[row['kind'] for row in rows if row['kind'] in ('execution','generation_retired','generation_recorded','generation_identity','stale_fence','stale_attempt','generation_dependency','primary_rebuilt','generation_execution')];require(actual_order==['execution','generation_retired','generation_recorded','generation_identity','stale_fence','stale_attempt','generation_dependency','primary_rebuilt','generation_execution'],'lifecycle evidence order');require(lifecycle_admission['status']=='RETIRED_SECONDARY_RERECORD_PRIMARY_REBUILD_VERIFIED','generation lifecycle/oracle')
  report['cases'][mode]={'records':rec,'lifecycle_admission':lifecycle_admission,'secondary_graphics':secondary_graphics,'admission':admission,'attachment_admission':attachment_admission,'diagnostics':r.stderr.decode().splitlines(),'exit_code':r.returncode,'stdout_sha256':sha(a.output/(mode+'.stdout')),'stderr_sha256':sha(a.output/(mode+'.stderr')),'normative':entries['VUID-vkQueueSubmit-pCommandBuffers-00070'] if mode.startswith('lifecycle') else entries[rules.VUID] if expected else None}
 require(all(c['records']['identity']==report['cases']['good']['records']['identity'] for c in report['cases'].values()),'identity changed');report['status']='BOUNDED_SECONDARY_DRAW_PASS';report['limitations']=['Original repository-authored fault, not external production bug.','CPU ICD only; no mobile/hardware/performance proof.','Wrong-output is independent CPU expectation inversion, not a Vulkan defect.','Execute callback abort discards primary command buffer, no invalid submission.','Standalone cohort; not included in previous five-chain delivery bundle.','No full VK03/VK10, concurrency or pending secondary reset/reuse acceptance.']
 require(report['source_sha256']==sha(source) and report['runner_sha256']==sha(__file__) and report['rules_sha256']==sha(rules.__file__) and report['draw_rules_sha256']==sha(draw_rules.__file__) and report['attachment_rules_sha256']==sha(attachment_rules.__file__),'sources changed');
 for stage,sh in shaders.items():require(sh['source_sha256']==sha(source.with_name('main.'+stage)),'shader source changed')
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
