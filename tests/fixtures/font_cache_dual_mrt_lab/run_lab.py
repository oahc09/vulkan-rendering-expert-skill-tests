import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
IMAGES={'B-initial':1,'B-new':5,'A-released':1,'B-after-A-destroyed':5,'A-rebuilt':3,'B-after-A-rebuilt':5}
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 cache=HERE.parent/'font_cache_churn_lab';run('prepare-cache-products',[sys.executable,cache/'run_lab.py','--out',out/'products']);build=out/'products/prepared/prepared/build';inputs=out/'products/inputs';before={str(p.relative_to(inputs)):sha(p) for p in inputs.rglob('*') if p.is_file()}
 engine=build/'combined_engine.hpp';s=engine.read_text();old='enabled.multiDrawIndirect = mdi;'
 if s.count(old)!=1:raise ValueError('engine hook')
 engine.write_text(s.replace(old,old+'if(!f2.features.independentBlend)throw std::runtime_error("independentBlend unavailable");enabled.independentBlend=VK_TRUE;'))
 header=build/'combined_pipeline.hpp';s=header.read_text()
 def change(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('pipeline hook '+old)
  s=s.replace(old,new)
 change('VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}};', 'VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{1,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{2,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}};')
 change('sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;','sub.preserveAttachmentCount=0;sub.pPreserveAttachments=nullptr;')
 change('VkPipelineColorBlendStateCreateInfo bs{','for(int i=1;i<3;i++){blends[i].blendEnable=VK_FALSE;blends[i].colorWriteMask=BAD_WRITE?15:0;}VkPipelineColorBlendStateCreateInfo bs{')
 header.write_text('#ifndef BAD_WRITE\n#define BAD_WRITE 0\n#endif\n'+s)
 combined=HERE.parent/'text_combined_lifecycle_lab/main.cpp';s=combined.read_text();marker='int main(int argc,char**argv)'
 if s.count(marker)!=1:raise ValueError('source hook')
 s=s[:s.index(marker)]
 def owner(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('ownership hook')
  s=s.replace(old,new)
 owner('struct PageResources {Image image{};', 'struct PageResources {VkDevice owner{};Image image{};')
 owner('p->generation=gen;', 'p->generation=gen;p->owner=v.device;')
 owner('if(!p.live||p.canceled||!p.uploadComplete', 'if(p.owner!=v.device||!p.live||p.canceled||!p.uploadComplete')
 for op in ('cancel','retire'):owner('void '+op+'(PageResources& p){','void '+op+'(PageResources& p){if(p.owner!=v.device)throw std::runtime_error("foreign device page");')
 owner('const std::vector<float>& mask){auto& s=begin();','const std::vector<float>& mask){if(p.owner!=v.device)throw std::runtime_error("foreign device page");auto& s=begin();')
 owner('if(!p.live)throw std::runtime_error("dead page route");','if(p.owner!=v.device)throw std::runtime_error("foreign device page");if(!p.live)throw std::runtime_error("dead page route");')
 (build/'dual_pending.hpp').write_text(s)
 run('shader',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'coverage.frag','-o',build/'shaders/coverage.frag.spv']);run('spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 for name,flags in [('dual',[]),('bad-write',['-DBAD_WRITE=1'])]:
  run('compile-'+name,cmd+flags+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/name]);log=run(name,[build/name,build/'shaders',inputs,out/name])
  if 'CACHE_DUAL_MRT_PASS validation_enabled=1 logical_devices_created=3' not in log:raise ValueError('receipt')
 q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad');c=load(cache/'run_lab.py','cache_aux');rows=[]
 for name,index in IMAGES.items():
  c.aux(out/'dual'/name);r=q.verify(inputs/str(index),out/'dual'/name);r['image']=name;rows.append(r)
 c.aux(out/'dual/B-wrong-route')
 try:q.verify(inputs/'1',out/'dual/B-wrong-route')
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('wrong route accepted')
 for name in list(IMAGES)+['B-wrong-route']:
  try:c.aux(out/'bad-write'/name)
  except ValueError as e:
   if 'aux sentinel' not in str(e):raise
  else:raise ValueError('write mask negative accepted')
 events=[json.loads(x) for x in (out/'dual/events.jsonl').read_text().splitlines()]
 expected=[('A_gated',True,0,-1,0),('B_initial',True,1,0,1),('B_canceled',True,2,0,1),('B_new',True,3,2,1),('A_destroyed',False,3,2,1),('B_continued',False,4,2,1),('A_rebuilt',False,4,2,1),('B_final',False,5,2,1)]
 if events[:-1]!=[dict(phase=phase,A_pending=p,B_completed=n,B_generation=g,B_live_pages=live) for phase,p,n,g,live in expected] or events[-1]!={'phase':'all_destroyed','B_completed':5}:raise ValueError('event accounting')
 if before!={str(p.relative_to(inputs)):sha(p) for p in inputs.rglob('*') if p.is_file()}:raise ValueError('CPU input changed')
 summary={'status':'PASS','validation_enabled':True,'logical_devices_created':3,'simultaneously_live_devices':2,'positive_images':6,'diagnostic_wrong_route_images':1,'active_color_attachments':3,'rows':rows,'events':events,'cache_inputs_immutable':True,'pause_guard_no_submission':True,'wrong_route_rejected':True,'bad_write_rejected_images':7,'limits':['same configured software implementation, not different physical GPUs or real Surfaces','CPU cache products pre-generated; not concurrent CPU/GPU production','B cancel occurs after upload completion, not pending B cancellation','active MRT but no depth/stencil/clip','fixed page sizes; no growth or full native allocator cleanup','A gate blocks submit, no simultaneous shader execution claim']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',HERE/'coverage.frag',combined,cache/'run_lab.py']},'generated':{str(p):sha(p) for p in [engine,header,build/'dual_pending.hpp',build/'dual',build/'bad-write']},'product_provenance':json.loads((out/'products/local-provenance.json').read_text()),'inputs':before},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
