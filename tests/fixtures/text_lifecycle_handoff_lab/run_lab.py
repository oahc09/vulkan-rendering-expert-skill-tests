#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('hook drift '+a)
 return s.replace(a,b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(path):
 ref=[[.16,.32,.48,1.] for _ in range(W*H)];glyphs=json.loads(path.read_text())['glyphs'];occupied=set()
 for g in glyphs:
  dx,dy=g['destination'];w,h=g['size']
  for y in range(h):
   for x in range(w):
    xx,yy=dx+x,dy+y
    if 0<=xx<W and 0<=yy<H:
     i=yy*W+xx;a=g['pixels'][y*w+x]*.75
     if a:occupied.add(i)
     ref[i]=[(.9,.5,.2)[c]*a+ref[i][c]*(1-a) for c in range(3)]+[1.]
 post={y*W+x for y in range(24,40) for x in range(34,54)}
 for i in post:ref[i]=[.56,.24,.08,1.]
 counts={'visible_overlay':len(occupied-post),'post_over_overlay':len(occupied&post),'pre_only':W*H-len(occupied|post)}
 if min(counts.values())<=0:raise ValueError('hidden stage ROI')
 return [x for p in ref for x in p],counts
def floats(p):
 b=p.read_bytes()
 if len(b)!=W*H*16:raise ValueError('size')
 a=struct.unpack('<12740f',b)
 if not all(math.isfinite(v) for v in a):raise ValueError('finite')
 return a
def auxiliaries(folder):
 for n,t in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(x!=t[i%4] for i,x in enumerate(floats(folder/(n+'.rgba32f')))):raise ValueError('sentinel mismatch')
def image_verify(folder,path):
 auxiliaries(folder)
 ref,counts=reference(path);v=floats(folder/'color.rgba32f');err=max(abs(a-b) for a,b in zip(v,ref))
 if err>1e-6:raise ValueError('composition mismatch')
 return {'max_error':err,'tolerance':1e-6,'roi_pixels':counts}
def verify(out):
 events=[json.loads(x) for x in (out/'frames/events.jsonl').read_text().splitlines()]
 phases=[dict(phase='cancel_B_pending',published=0,A_pending=True,B_upload_pending=True,live_pages=2),dict(phase='cancel_B_retired',published=0,live_pages=1),dict(phase='new_B_published_pending',published=2,live_pages=2),dict(phase='old_A_retired',published=2,live_pages=1)]
 if events!=phases:raise ValueError('retirement/publication events mismatch')
 rows=[]
 for name,path in [('old-A',out/'reference.json'),('route-after-cancel',out/'reference.json'),('new-B',out/'new-reference/reference.json')]:
  row=image_verify(out/'frames'/name,path);row['stage']=name;rows.append(row)
 try:image_verify(out/'frames/wrong-cancel-route',out/'reference.json')
 except ValueError as e:
  if str(e)!='composition mismatch':raise
 else:raise ValueError('wrong route accepted')
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args,expected=0,timeout=120):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 joint=HERE.parent/'text_joint_lifecycle_lab';combined=HERE.parent/'text_combined_lifecycle_lab'
 run('prepare',[sys.executable,joint/'run_lab.py','--out',out/'prepared'],timeout=180)
 prepared=out/'prepared';build=prepared/'prepared/prepared/build';shaders=build/'joint-shaders-0'
 shutil.copyfile(prepared/'reference.json',out/'reference.json');shutil.copytree(prepared/'new-reference',out/'new-reference')
 _,counts=reference(out/'reference.json');(out/'conditions.json').write_text(json.dumps({'tolerance':1e-6,'roi_pixels':counts,'post_rect':[34,24,20,16],'pre':[.16,.32,.48,1],'post':[.56,.24,.08,1]},indent=2))
 s=(build/'combined_pipeline.hpp').read_text();s=replace(s,'struct TextLab: Vulkan {','struct TextLab: Vulkan {\n Image sceneImage;VkDescriptorSet sceneSet{};VkPipeline scenePipeline{};size_t sceneUpload,sceneVertices;')
 s=replace(s,'dp.maxSets=3;','dp.maxSets=4;');s=replace(s,'VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,3','VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,4')
 s=replace(s,'    upload=buffers.size();','''    sceneImage=image(VK_FORMAT_R32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    sceneUpload=buffers.size();buffers.push_back(buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT));std::vector<float> sm(width*height,.8f);std::memcpy(buffers[sceneUpload].map,sm.data(),sm.size()*4);
    float sv[]={-1,-1,0,0,1,-1,1,0,-1,1,0,1,-1,1,0,1,1,-1,1,0,1,1,1,1};sceneVertices=buffers.size();buffers.push_back(buffer(sizeof(sv),VK_BUFFER_USAGE_VERTEX_BUFFER_BIT));std::memcpy(buffers[sceneVertices].map,sv,sizeof(sv));
    upload=buffers.size();''')
 s=replace(s,'    VkAttachmentDescription attachments[3]{};','VK(vkAllocateDescriptorSets(device,&sa,&sceneSet));imageInfo.imageView=sceneImage.view;write.dstSet=sceneSet;vkUpdateDescriptorSets(device,1,&write,0,nullptr);\n    VkAttachmentDescription attachments[3]{};')
 s=replace(s,'    auto result=vkCreateGraphicsPipelines','VkDynamicState states[]={VK_DYNAMIC_STATE_VIEWPORT,VK_DYNAMIC_STATE_SCISSOR};VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};dyn.dynamicStateCount=2;dyn.pDynamicStates=states;pi.pDynamicState=&dyn;\n    auto result=vkCreateGraphicsPipelines')
 needle='vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);'
 s=replace(s,needle,'''VK(result);auto sf=shader("handoff_scene.frag");stages[1].module=sf;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&scenePipeline));vkDestroyShaderModule(device,sf,nullptr);'''+needle+'''
    begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT|VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,VK_ACCESS_TRANSFER_READ_BIT|VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT);transition(sceneImage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,0,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);VkBufferImageCopy cp{};cp.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};cp.imageExtent={65,49,1};vkCmdCopyBufferToImage(cb,buffers[sceneUpload].buffer,sceneImage.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&cp);transition(sceneImage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);submit();''')
 s=replace(s,'vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyPipeline(device,scenePipeline,nullptr);');s=replace(s,'for(auto im:{target,velocity,ids,coverage})','for(auto im:{target,velocity,ids,coverage,sceneImage})');(build/'combined_pipeline.hpp').write_text(s)
 s=(combined/'main.cpp').read_text();start='vkCmdBeginRenderPass(s.cb,&ri,VK_SUBPASS_CONTENTS_INLINE);';end='vkCmdEndRenderPass(s.cb);'
 if s.count(start)!=1 or s.count(end)!=1:raise ValueError('draw hook drift')
 beg=s.index(start);stop=s.index(end,beg)+len(end)
 s=s[:beg]+'''vkCmdBeginRenderPass(s.cb,&ri,VK_SUBPASS_CONTENTS_INLINE);
 VkDeviceSize offset=0;auto bind=[&](VkPipeline pipeline,VkDescriptorSet set,VkBuffer vb,VkViewport vp,VkRect2D sc,const std::array<float,4>&ink,bool post){
 if(!post||!OMIT_POST){vkCmdBindPipeline(s.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,pipeline);vkCmdBindDescriptorSets(s.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,v.textLayout,0,1,&set,0,nullptr);vkCmdBindVertexBuffers(s.cb,0,1,&vb,&offset);vkCmdSetViewport(s.cb,0,1,&vp);vkCmdSetScissor(s.cb,0,1,&sc);}
 vkCmdPushConstants(s.cb,v.textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,ink.data());};
 bind(v.scenePipeline,v.sceneSet,v.buffers[v.sceneVertices].buffer,{0,0,65,49,0,1},{{0,0},{65,49}},{.2,.4,.6,1},false);vkCmdDraw(s.cb,6,1,0,0);
 bind(v.textPipeline,p.set,s.vertices.buffer,{0,0,65,49,0,1},{{0,0},{65,49}},{.9,.5,.2,.75},false);vkCmdDraw(s.cb,vertices.size()/4,1,0,0);
 bind(v.scenePipeline,v.sceneSet,v.buffers[v.sceneVertices].buffer,{30,20,30,24,0,1},{{34,24},{20,16}},{.7,.3,.1,.75},true);vkCmdDraw(s.cb,6,1,0,0);
 vkCmdEndRenderPass(s.cb);'''+s[stop:]
 s='#ifndef OMIT_POST\n#define OMIT_POST 0\n#endif\n'+s;(build/'lifecycle_handoff.cpp').write_text(s)
 run('scene-shader',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'scene.frag','-o',shaders/'handoff_scene.frag.spv']);run('scene-validate',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',shaders/'handoff_scene.frag.spv'])
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 for name,flags in [('lifecycle_handoff',[]),('omit_post',['-DOMIT_POST=1'])]:run('compile-'+name,cmd+flags+[build/'lifecycle_handoff.cpp','-l:libvulkan.so.1','-o',build/name])
 args=[shaders,prepared/'prepared/prepared/atlas.f32',prepared/'vertices.f32']
 log=run('positive',[build/'lifecycle_handoff',*args,out/'frames'])
 if 'COMBINED_PASS validation_enabled=1' not in log or 'COMBINED_RESOURCES_DESTROYED' not in log:raise ValueError('validation/cleanup receipt')
 rows=verify(out)
 bad=out/'omit-post';bad.mkdir();shutil.copyfile(out/'reference.json',bad/'reference.json');shutil.copytree(out/'new-reference',bad/'new-reference');run('omit-post',[build/'omit_post',*args,bad/'frames'])
 for folder in (bad/'frames').iterdir():
  if folder.is_dir():auxiliaries(folder)
 try:verify(bad)
 except ValueError as e:
  if str(e)!='composition mismatch':raise
 else:raise ValueError('post omission not detected')
 aborted=run('abort-pending',[build/'lifecycle_handoff',*args,out/'aborted','--abort-pending'],1)
 if 'COMBINED_PENDING_CLEANUP_OK' not in aborted or 'INTENTIONAL_COMBINED_PENDING_CLEANUP' not in aborted:raise ValueError('pending cleanup receipt')
 summary={'status':'PASS','validation_enabled':True,'lifecycle_render_submissions':4,'positive_verified_images':3,'wrong_route_diagnostic_images':1,'draws_per_render_submission':3,'positive_verified_draws':9,'renderpasses_per_render_submission':1,'active_color_attachments':3,'clip_layers':3,'rows':rows,'negative_checks':['actual canceled descriptor route','actual omit post state rebinding','controlled pending gate release and cleanup'],'limits':['single software Vulkan device and queue','ALL_COMMANDS gate is pending not shader execution','one scene upload setup submission plus three atlas uploads distinct from four render submissions','no depth/stencil or full arbitrary renderer state','no general allocation/device loss cleanup','no target-device Live acceptance']};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 sources=[HERE/'run_lab.py',HERE/'scene.frag',combined/'main.cpp',joint/'run_lab.py',joint/'joint.frag'];generated=[build/'combined_pipeline.hpp',build/'lifecycle_handoff.cpp',build/'lifecycle_handoff',build/'omit_post',shaders/'handoff_scene.frag.spv']
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in sources},'generated':{str(p):sha(p) for p in generated},'prepared_receipt':json.loads((prepared/'local-provenance.json').read_text())},indent=2))
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','preview')
 for name in ['old-A','route-after-cancel','new-B']:
  rgba=floats(out/'frames'/name/'color.rgba32f');preview.png(out/'frames'/name/'preview.png',W,H,bytes(round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055)) for i,v in enumerate(rgba) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
