"""Real vertex+fragment graphics pipeline and checkerboard draw readback; CPU ICD only."""
import argparse,hashlib,json,os,pathlib,subprocess,uuid,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));import dynamic_draw19 as rules;import dynamic_color19 as attachment_rules
SHA='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument('--tools',required=True);p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--validusage',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 require(sha(a.validusage)==SHA,'unpaired specification');spec=json.loads(pathlib.Path(a.validusage).read_text());entries={e['vuid']:e for name in ('vkCmdDraw',) for group in spec['validation'][name].values() for e in group}
 lm=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';layer=json.loads(lm.read_text())['layer'];require(layer['api_version']=='1.4.309','unpaired layer')
 source=pathlib.Path(__file__).with_name('probe.c');exe=a.output/'probe';r=subprocess.run(['gcc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+a.include,str(source),a.loader,'-o',str(exe)],capture_output=True,timeout=60)
 (a.output/'build.stdout').write_bytes(r.stdout);(a.output/'build.stderr').write_bytes(r.stderr);require(r.returncode==0,'compile failed')
 report={'run_id':str(uuid.uuid4()),'source_sha256':sha(source),'runner_sha256':sha(__file__),'rules_sha256':sha(rules.__file__),'attachment_rules_sha256':sha(attachment_rules.__file__),'binary_sha256':sha(exe),'loader_sha256':sha(a.loader),'icd_manifest_sha256':sha(os.environ['VK_DRIVER_FILES']),'layer_manifest_sha256':sha(lm),'spec_sha256':SHA,'spec_version':spec['version info'],'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'cases':{}}
 shaders={}
 for stage in ('vert','frag'):
  src=source.with_name('main.'+stage);spv=a.output/(stage+'.spv');logs={}
  for name,cmd in [('compile',[str(pathlib.Path(a.tools)/'glslangValidator'),'-V','--target-env','vulkan1.1',str(src),'-o',str(spv)]),('validate',[str(pathlib.Path(a.tools)/'spirv-val'),'--target-env','vulkan1.1',str(spv)]),('disassemble',[str(pathlib.Path(a.tools)/'spirv-dis'),str(spv)])]:
   r=subprocess.run(cmd,capture_output=True,timeout=60);base=a.output/(stage+'-'+name);pathlib.Path(str(base)+'.stdout').write_bytes(r.stdout);pathlib.Path(str(base)+'.stderr').write_bytes(r.stderr);require(r.returncode==0,'shader tool failure');logs[name]={'exit_code':r.returncode,'stdout_sha256':sha(str(base)+'.stdout'),'stderr_sha256':sha(str(base)+'.stderr'),'tool_sha256':sha(cmd[0]),'version':subprocess.check_output([cmd[0],'--version'],text=True)}
  shaders[stage]={'source_sha256':sha(src),'binary_sha256':sha(spv),'target_env':'vulkan1.1','tools':logs}
 report['shaders']=shaders
 for mode in ('good','format','wrong-output'):
  r=subprocess.run([str(exe),mode,str(a.output/'vert.spv'),str(a.output/'frag.spv')],capture_output=True,timeout=30);(a.output/(mode+'.stdout')).write_bytes(r.stdout);(a.output/(mode+'.stderr')).write_bytes(r.stderr);require(r.returncode==(6 if mode=='wrong-output' else 0),'runtime failure')
  rows=[json.loads(x) for x in r.stdout.decode().splitlines()];rec={x['kind']:x for x in rows};require(len(rows)==len(rec),'duplicate records');i=rec['identity'];require(i['deviceType']==4 and i['apiVersion']>=4206592 and i['layerSpec']==4210997 and i['layerImplementation']==int(layer['implementation_version']),'runtime identity');attachment_admission=attachment_rules.admit(rec['manifest']);require(attachment_admission['status']=='CONFIG_WITHIN_SCOPE','base attachment admission');admission=rules.admit(rec['pipeline'],rec['manifest'],rec['limits']);expected=[rules.VUID] if mode=='format' else [];require(admission['vuids']==expected,'actual rule pairing');require(r.stderr.decode().splitlines()==[mode+' '+x for x in expected],'unexpected VVL');require(rec['final']=={'kind':'final','errors':len(expected),'rc':6 if mode=='wrong-output' else 0},'cleanup failure');ex=rec['execution']
  require(all(rec[k]['memoryTypeBits']&(1<<rec[k]['selectedType']) for k in ('image_allocation','buffer_allocation')) and rec['buffer_allocation']['selectedFlags']&6==6,'memory selection')
  if mode=='format':require(ex=={'kind':'execution','submitted':False,'discarded':True},'invalid draw submitted')
  else:require(ex['submitted'] is True and ex['fenceCompleted'] is True and ex['pixels']==rules.reference(),'independent checker oracle')
  report['cases'][mode]={'records':rec,'admission':admission,'attachment_admission':attachment_admission,'diagnostics':r.stderr.decode().splitlines(),'exit_code':r.returncode,'stdout_sha256':sha(a.output/(mode+'.stdout')),'stderr_sha256':sha(a.output/(mode+'.stderr')),'normative':entries[rules.VUID] if expected else None}
 report['status']='BOUNDED_DYNAMIC_DRAW_PASS';report['limitations']=['Original repository-authored fault, not external production bug.','CPU ICD only; no mobile/hardware/performance proof.','Wrong-output is independent CPU expectation inversion, not a Vulkan defect.','Draw callback abort discards command buffer, no invalid submission.','Standalone cohort; not included in previous five-chain delivery bundle.','No full VK10 or all-domain L1/L2 acceptance.']
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
