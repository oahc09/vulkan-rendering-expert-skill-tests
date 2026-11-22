"""Run real combined-sampler upload→sample→storage image→readback."""
import argparse,hashlib,importlib.util,json,os,pathlib,re,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[2];SRC=pathlib.Path(__file__).resolve().parent
SPEC='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(x,msg):
 if not x:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser()
 for k in ('tools','include','loader','validusage','output'):p.add_argument('--'+k,type=pathlib.Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);os.environ['VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC']='true'
 spec=importlib.util.spec_from_file_location('sampling',ROOT/'tools/texture_sampling19.py');rule=importlib.util.module_from_spec(spec);spec.loader.exec_module(rule)
 r={'run_id':str(uuid.uuid4()),'scope':'Authored single CPU ICD, RGBA8_UNORM nearest explicit LOD0 normalized clamp; no linear/sRGB/mip/anisotropy/physical hardware claim. SyncVal shader access heuristic enabled, not precise shader memory analysis.','sources':{f:sha(SRC/f) for f in ('probe.c','compute.comp','normative.json','run.py')},'rule_sha256':sha(ROOT/'tools/texture_sampling19.py'),'tools':{},'cases':{}}
 def run(label,cmd,expected=0):
  x=subprocess.run([str(v) for v in cmd],capture_output=True,timeout=60);(a.output/(label+'.stdout')).write_bytes(x.stdout);(a.output/(label+'.stderr')).write_bytes(x.stderr);log={'exit_code':x.returncode,'stdout_sha256':sha(a.output/(label+'.stdout')),'stderr_sha256':sha(a.output/(label+'.stderr'))};need(x.returncode==expected,label+' exit mismatch');return x,log
 need(sha(a.validusage)==SPEC,'normative cohort mismatch');corpus=json.loads(a.validusage.read_text());norm=json.loads((SRC/'normative.json').read_text());entry=norm['entries'][0];need(norm['source_sha256']==SPEC and norm['api_version']==corpus['version info']['api version']=='1.4.309' and {k:v for k,v in entry.items() if k not in ('owner','condition')} in corpus['validation'][entry['owner']][entry['condition']],'normative entry mismatch');r['normative_sha256']=SPEC
 layerpath=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';layer=json.loads(layerpath.read_text())['layer'];version=list(map(int,layer['api_version'].split('.')));layer_spec=version[0]<<22|version[1]<<12|version[2]
 r.update(loader_sha256=sha(a.loader),icd_manifest_sha256=sha(os.environ['VK_DRIVER_FILES']),layer_manifest_sha256=sha(layerpath))
 for name in ('glslangValidator','spirv-val','spirv-dis'):
  x,log=run(name+'-version',[a.tools/name,'--version']);r['tools'][name]={'binary_sha256':sha(a.tools/name),'version':x.stdout.decode().strip(),'log':log}
 spv=a.output/'compute.spv';asm=a.output/'compute.spvasm';binary=a.output/'probe'
 _,r['compile']=run('shader-compile',[a.tools/'glslangValidator','-V','--target-env','vulkan1.1',SRC/'compute.comp','-o',spv]);_,r['validate']=run('shader-val',[a.tools/'spirv-val','--target-env','vulkan1.1',spv]);_,r['disassemble']=run('shader-dis',[a.tools/'spirv-dis',spv,'-o',asm]);text=asm.read_text();need(all(x in text for x in ('OpImageSampleExplicitLod','OpImageWrite','Rgba8','DescriptorSet 0','Binding 0','Binding 1','LocalSize 1 1 1')),'shader structure missing');r.update(spirv_sha256=sha(spv),disassembly_sha256=sha(asm))
 _,r['build']=run('build',['gcc','-Wall','-Wextra','-Werror','-I'+str(a.include),SRC/'probe.c',a.loader,'-o',binary]);r['binary_sha256']=sha(binary)
 identities=[]
 for mode,expected in (('normal',0),('bad-sampler',0),('wrong-output',6)):
  x,log=run(mode,[binary,mode,spv],expected);result=json.loads(x.stdout);facts={}
  for line in x.stderr.decode().splitlines():
   if ' ' in line:
    k,v=line.split(' ',1)
    if v.startswith(('{','[')):facts.setdefault(k,[]).append(json.loads(v))
  def one(k):need(len(facts.get(k,[]))==1,'singleton '+k);return facts[k][0]
  identity=one('IDENTITY');need(identity['device_type']==4 and identity['api']>>29==0 and identity['api']>=(1<<22|1<<12) and identity['layer_spec']==layer_spec and identity['layer_impl']==int(layer['implementation_version']),'runtime identity');identities.append(identity)
  query=one('IMAGE_QUERY');need(query==dict(format=37,imageType=1,tiling=0,usage=15,flags=0,result=0,samples=query['samples'],maxLevels=query['maxLevels'],maxLayers=query['maxLayers']) and query['samples']&1 and query['maxLevels']>=1 and query['maxLayers']>=1,'format query')
  cap=one('CAPABILITY');need(cap['format']==37 and cap['required_features']==49155 and cap['optimal_features']&cap['required_features']==cap['required_features'] and cap['max_width']>=4 and cap['max_height']>=4,'format caps');limits=one('LIMITS');need(all(limits[k]>=1 for k in ('samplers','sampledImages','storageImages','setSamplers','setSampled','setStorage','groupsZ')) and limits['groupsX']>=4 and limits['groupsY']>=4,'limits');need(one('QUEUE')['flags']&2,'compute queue')
  need(len(facts['MEMORY'])==2 and len(facts['IMAGE_MEMORY'])==2 and len(facts['IMAGE_CREATE'])==2,'memory/image count')
  for i,b in enumerate(facts['MEMORY']):need(b['buffer']==i and b['bits']&(1<<b['type']) and b['flags']&6==6 and b['size']>=64,'coherent buffer')
  for i,b in enumerate(facts['IMAGE_MEMORY']):need(b['image']==i and b['bits']&(1<<b['type']) and b['size']>=64,'image memory')
  for i,b in enumerate(facts['IMAGE_CREATE']):need(b==dict(image=i,format=37,usage=15,width=4,height=4,samples=1,levels=1,layers=1),'image scope')
  need(len(facts.get('VIEW',[]))==2 and all(b==dict(image=i,format=37,type=1,r=0,g=0,b=0,a=0,aspect=1,baseMip=0,levels=1,baseLayer=0,layers=1) for i,b in enumerate(facts['VIEW'])),'identity views')
  texture=[(255 if x==0 else 0)|((255 if y<2 else 0)<<8)|((255 if x<1+y%3 else 0)<<16)|0xff000000 for y in range(4) for x in range(4)];need(one('INPUT')==texture,'uploaded texture')
  admission=rule.sampler(one('SAMPLER'));diags=re.findall(r'DIAGNOSTIC phase=(\S+) id=(\S+)',x.stderr.decode())
  if mode=='bad-sampler':
   need(admission=={'status':'REJECTED','vuids':[rule.VUID]} and diags==[('sampler-create',rule.VUID)] and result['submitted'] is False and result['errors']==1 and 'SAMPLER_RESULT -1000011001' in x.stderr.decode() and not facts.get('COMPLETION'),'safe sampler negative')
  else:
   need(admission=={'status':'NEAREST_CLAMP_SCOPE','vuids':[]} and not diags and result['errors']==0 and result['submitted'] is True and result['pixels']==rule.reference(),'pixel oracle')
   need(one('COMPLETION')==dict(fence_wait='SUCCESS',host_barrier_src_access=4096,host_barrier_dst_access=8192),'completion')
   need(facts['DESCRIPTOR']==[dict(set=0,binding=0,type=1,count=1,stage=32,imageLayout=5,image=0),dict(set=0,binding=1,type=3,count=1,stage=32,imageLayout=1,image=1)],'descriptor interface')
   barriers=facts['BARRIER'];need(len(barriers)==4 and [(b['oldLayout'],b['newLayout'],b['srcAccess'],b['dstAccess'],b['srcStage'],b['dstStage']) for b in barriers]==[(0,1,0,4096,1,4096),(0,1,0,64,1,2048),(1,5,4096,32,4096,2048),(1,6,64,2048,2048,4096)],'image dependencies')
   need([b['image'] for b in barriers]==[0,1,0,1] and [b['phase'] for b in barriers]==['initial-layouts','initial-layouts','upload','readback'] and all({k:b[k] for k in ('aspect','baseMip','levels','baseLayer','layers')}==dict(aspect=1,baseMip=0,levels=1,baseLayer=0,layers=1) for b in barriers),'barrier objects/subresources')
   need(one('COPY_UPLOAD')==dict(image=0,layout=1,width=4,height=4,depth=1,aspect=1,mip=0,baseLayer=0,layerCount=1) and one('COPY_READBACK')==dict(image=1,layout=6,width=4,height=4,depth=1),'copy manifests')
   if mode=='wrong-output':need((rule.reference()[0]^1)!=result['pixels'][0],'wrong oracle must differ')
  r['cases'][mode]=dict(log=log,result=result,facts=facts,admission=admission,diagnostics=diags)
 need(identities[0]==identities[1]==identities[2],'identity changed');need(r['sources']=={f:sha(SRC/f) for f in r['sources']} and r['rule_sha256']==sha(ROOT/'tools/texture_sampling19.py'),'source changed');r['status']='BOUNDED_NEAREST_COMBINED_SAMPLER_PASS';(a.output/'summary.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
