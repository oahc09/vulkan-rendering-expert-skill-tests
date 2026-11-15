#!/usr/bin/env python3
"""One real Vulkan pass, three draws, bounded explicit state handoff."""
import argparse,hashlib,importlib.util,json,math,os,shutil,struct,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
MODES=['pipeline','descriptor','vertex','viewport','scissor','all']
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('hook drift: '+a)
 return s.replace(a,b)
def expected():
 pixels=[];counts={'pre_only':0,'overlay_visible':0,'post_over_overlay':0,'post_without_overlay':0}
 for y in range(H):
  for x in range(W):
   X,Y=x+.5,y+.5;rgb=[.16,.32,.48,1.];overlay=False
   # Overlay half-NDC quad in viewport (8,6,40,32): [18,38)x[14,30).
   if 18<=X<38 and 14<=Y<30 and 10<=X<44 and 8<=Y<36:
    tx=math.floor((X-18)/20*65);ty=math.floor((Y-14)/16*49)
    c=.5 if 6<=tx<59 and 5<=ty<44 and not(22<=tx<43 and 17<=ty<32) else 0
    a=c*.75;rgb=[(.9,.5,.2)[i]*a+rgb[i]*(1-a) for i in range(3)]+[1.];overlay=c>0
   post=34<=X<54 and 24<=Y<40 # post viewport 30,20,30,24 fully covers scissor
   if post:rgb=[.56,.24,.08,1.];counts['post_over_overlay' if overlay else 'post_without_overlay']+=1
   else:counts['overlay_visible' if overlay else 'pre_only']+=1
   pixels.extend(rgb)
 if not all(counts.values()):raise ValueError('invisible stage ROI')
 return pixels,counts
def floats(p):
 b=p.read_bytes()
 if len(b)!=W*H*16:raise ValueError('size')
 v=struct.unpack('<'+str(W*H*4)+'f',b)
 if not all(math.isfinite(x) for x in v):raise ValueError('finite')
 return v
def verify(folder):
 v=floats(folder/'color.f32');ref,counts=expected();err=max(abs(a-b) for a,b in zip(v,ref))
 if err>1e-6:raise ValueError('composition mismatch')
 auxiliaries(folder)
 return {'max_error':err,'tolerance':1e-6,'roi_pixels':counts}
def auxiliaries(folder):
 for n,t in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=t[i%4] for i,v in enumerate(floats(folder/(n+'.f32')))):raise ValueError('active sentinel changed')
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);ref,counts=expected()
 (out/'conditions.json').write_text(json.dumps({'tolerance':1e-6,'modes':MODES,'roi_pixels':counts,'scope':'synthetic coverage state diagnostic'},indent=2))
 def run(name,cmd):
  r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 base=HERE.parent/'text_vector_lab';build=out/'build';run('base',[base/'build.sh',build])
 engine=HERE.parent/'engine_scale_lab/main.cpp';s=replace(engine.read_text(),'enabled.multiDrawIndirect = mdi;','enabled.multiDrawIndirect = mdi;if(!f2.features.independentBlend)throw std::runtime_error("independentBlend required");enabled.independentBlend=VK_TRUE;');(build/'engine.hpp').write_text(s)
 s=(base/'main.cpp').read_text();s=replace(s,'../engine_scale_lab/main.cpp',str(build/'engine.hpp'));s=replace(s,'int main(int argc,char** argv)','int unused_original_main(int argc,char** argv)')
 s=replace(s,'struct TextLab: Vulkan {','static std::string gMode;\nstruct TextLab: Vulkan {\n Image sceneImage;VkDescriptorSet sceneSet{};VkPipeline scenePipeline{};size_t sceneUpload,fullVertex,halfVertex;')
 s=replace(s,'    upload=buffers.size();','''    sceneImage=image(VK_FORMAT_R32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    sceneUpload=buffers.size();buffers.push_back(buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT));std::vector<float> sceneMask(width*height,.8f);std::memcpy(buffers[sceneUpload].map,sceneMask.data(),sceneMask.size()*4);
    auto vertices=[&](float lo,float hi){float v[]={lo,lo,0,0,hi,lo,1,0,lo,hi,0,1,lo,hi,0,1,hi,lo,1,0,hi,hi,1,1};size_t i=buffers.size();buffers.push_back(buffer(sizeof(v),VK_BUFFER_USAGE_VERTEX_BUFFER_BIT));std::memcpy(buffers[i].map,v,sizeof(v));return i;};fullVertex=vertices(-1,1);halfVertex=vertices(-.5,.5);
    upload=buffers.size();''')
 s=replace(s,'VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};','VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,2};');s=replace(s,'dp.maxSets=1;','dp.maxSets=2;')
 s=replace(s,'    VkAttachmentDescription attachments[3]{};','VK(vkAllocateDescriptorSets(device,&sa,&sceneSet));imageInfo.imageView=sceneImage.view;write.dstSet=sceneSet;vkUpdateDescriptorSets(device,1,&write,0,nullptr);\n    VkAttachmentDescription attachments[3]{};')
 s=replace(s,'{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}','{1,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{2,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}');s=replace(s,'sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;','')
 s=replace(s,'    VkPipelineInputAssemblyStateCreateInfo ia{','VkVertexInputBindingDescription vb{0,16,VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription va[]={{0,0,VK_FORMAT_R32G32_SFLOAT,0},{1,0,VK_FORMAT_R32G32_SFLOAT,8}};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&vb;vi.vertexAttributeDescriptionCount=2;vi.pVertexAttributeDescriptions=va;\n    VkPipelineInputAssemblyStateCreateInfo ia{')
 s=replace(s,'    VkPipelineColorBlendStateCreateInfo bs{','for(int i=1;i<3;i++){blends[i].blendEnable=VK_FALSE;blends[i].colorWriteMask=0;}\n    VkPipelineColorBlendStateCreateInfo bs{')
 s=replace(s,'    auto result=vkCreateGraphicsPipelines','VkDynamicState states[]={VK_DYNAMIC_STATE_VIEWPORT,VK_DYNAMIC_STATE_SCISSOR};VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};dyn.dynamicStateCount=2;dyn.pDynamicStates=states;pi.pDynamicState=&dyn;\n    auto result=vkCreateGraphicsPipelines')
 needle='vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);'
 s=replace(s,needle,'VK(result);auto sceneFS=shader("handoff_scene.frag");stages[1].module=sceneFS;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&scenePipeline));vkDestroyShaderModule(device,sceneFS,nullptr);'+needle)
 s=replace(s,'    Image images[]={target,velocity,ids};','''    barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT);
    transition(sceneImage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,0,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);vkCmdCopyBufferToImage(cb,buffers[sceneUpload].buffer,sceneImage.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&copy);transition(sceneImage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
    Image images[]={target,velocity,ids};''')
 start='vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);';end='vkCmdEndRenderPass(cb);'
 if s.count(start)!=1 or s.count(end)!=1:raise ValueError('draw hook drift')
 beg=s.index(start);finish=s.index(end,beg)+len(end)
 s=s[:beg]+'''vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);
    VkDeviceSize offset=0;
    auto bind=[&](VkPipeline pipeline,VkDescriptorSet set,size_t vertex,VkViewport viewport,VkRect2D scissor,const std::array<float,4>&color,bool post){
      auto omitted=[&](const char* name){return post&&(gMode==name||gMode=="all");};
      if(!omitted("pipeline"))vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,pipeline);
      if(!omitted("descriptor"))vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textLayout,0,1,&set,0,nullptr);
      if(!omitted("vertex"))vkCmdBindVertexBuffers(cb,0,1,&buffers[vertex].buffer,&offset);
      if(!omitted("viewport"))vkCmdSetViewport(cb,0,1,&viewport);
      if(!omitted("scissor"))vkCmdSetScissor(cb,0,1,&scissor);
      vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,color.data());vkCmdDraw(cb,6,1,0,0);
    };
    bind(scenePipeline,sceneSet,fullVertex,{0,0,65,49,0,1},{{0,0},{65,49}},{.2,.4,.6,1},false);
    bind(textPipeline,textSet,halfVertex,{8,6,40,32,0,1},{{10,8},{34,28}},ink,false);
    bind(scenePipeline,sceneSet,fullVertex,{30,20,30,24,0,1},{{34,24},{20,16}},{.7,.3,.1,.75},true);
    vkCmdEndRenderPass(cb);'''+s[finish:]
 s=replace(s,'vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyPipeline(device,scenePipeline,nullptr);');s=replace(s,'for(auto im:{target,velocity,ids,coverage})','for(auto im:{target,velocity,ids,coverage,sceneImage})');(build/'handoff.hpp').write_text(s)
 for source,target in [('quad.vert','fullscreen.vert'),('overlay.frag','coverage.frag'),('scene.frag','handoff_scene.frag')]:
  run('compile-'+source,[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',HERE/source,'-o',build/'shaders'/(target+'.spv')]);run('validate-'+source,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',build/'shaders'/(target+'.spv')])
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'handoff'])
 for mode in ['normal']+MODES:
  log=run(mode,[build/'handoff',build/'shaders',out/mode,mode])
  if 'HANDOFF_PASS validation_enabled=1 draws=3 renderpasses=1 submissions=1' not in log:raise ValueError('missing receipt')
 numeric=verify(out/'normal');neg=[]
 for mode in MODES:
  auxiliaries(out/mode)
  try:verify(out/mode)
  except ValueError as e:
   if str(e)!='composition mismatch':raise
  else:raise ValueError('missing negative '+mode)
  v=floats(out/mode/'color.f32');neg.append({'mode':mode,'max_error':max(abs(x-y) for x,y in zip(v,ref)),'changed_pixels':sum(any(abs(v[i*4+c]-ref[i*4+c])>1e-6 for c in range(4)) for i in range(W*H))})
 summary={'status':'PASS','validation_enabled':True,'positive_draws':3,'positive_renderpasses':1,'positive_submissions':1,'active_color_attachments':3,'numeric':numeric,'negatives':neg,'scope':'synthetic coverage, explicit compatible state handoff, single software Vulkan pass; no depth or general renderer certification'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
 hashes=lambda paths:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 tools={}
 for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
  path=Path(shutil.which(os.environ.get(key,default)));tools[key]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'version':run('version-'+key,[path,'--version'])}
 drivers={}
 for name in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
  if name:
   path=Path(name);drivers.update(hashes([path]));lib=Path(json.loads(path.read_text())['ICD']['library_path'])
   if lib.is_absolute() and lib.is_file():drivers.update(hashes([lib]))
 layers={}
 for name in os.environ.get('VK_LAYER_PATH','').split(os.pathsep):
  if name:layers.update(hashes(list(Path(name).glob('*.json'))))
 revisions={'tests':run('revision-tests',['git','-C',ROOT,'rev-parse','HEAD','HEAD^{tree}'])}
 if os.environ.get('VULKAN_SKILL_ROOT'):revisions['skill']=run('revision-skill',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
 (out/'local-provenance.json').write_text(json.dumps({'sources':hashes([*HERE.glob('*.py'),*HERE.glob('*.cpp'),*HERE.glob('*.vert'),*HERE.glob('*.frag'),base/'main.cpp',engine]),'binary_and_generated':hashes([build/'handoff',build/'handoff.hpp',build/'engine.hpp',*list((build/'shaders').glob('*.spv'))]),'tools':tools,'drivers':drivers,'layers':layers,'revisions':revisions},indent=2))
 spec=importlib.util.spec_from_file_location('png',base/'run_lab.py');preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)
 v=floats(out/'normal/color.f32');preview.png(out/'normal/preview.png',W,H,bytes(round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for i,x in enumerate(v) if i%4!=3));print(json.dumps(summary))
if __name__=='__main__':main()
