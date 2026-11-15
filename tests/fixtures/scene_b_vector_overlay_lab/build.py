import os
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent/'scene_b_shared_world_lab'
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('hook '+a)
 return s.replace(a,b)
def build(b,run):
 s=(b/'active_lab_reused.hpp').read_text()
 s=replace(s,'VkPipeline labelPipeline{};','VkPipeline labelPipeline{},panelPipeline{};int vectorMode=0;')
 s=replace(s,'VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&labelPipeline));','VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&labelPipeline));ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&panelPipeline));')
 s=replace(s,'emit(sceneVB,12,6,3);','emit(sceneVB,12,6,3);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,panelPipeline);float panel[]={0,0,4,float(vectorMode)};vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,16,panel);vkCmdBindVertexBuffers(cb,0,1,&buffers[sceneVB].buffer,&zero);vkCmdDraw(cb,6,1,0,0);')
 s=replace(s,'vkDestroyPipeline(device,labelPipeline,nullptr);','vkDestroyPipeline(device,panelPipeline,nullptr);vkDestroyPipeline(device,labelPipeline,nullptr);');(b/'active_lab_reused.hpp').write_text(s)
 v=(BASE/'world.vert').read_text();v=replace(v,'gl_Position=vec4(q/vec2(65,49)*2-1,position.z/16,1);','gl_Position=pc.p.z==4?vec4(position.xy/vec2(65,49)*2-1,0,1):vec4(q/vec2(65,49)*2-1,position.z/16,1);')
 f=(BASE/'world.frag').read_text();f=replace(f,'void main(){',(HERE/'panel.glsl').read_text()+'\nvoid main(){');f=replace(f,'velocity=vec4(8);ids=vec4(9);','if(kind==4){if(!vectorPanel(gl_FragCoord.xy,int(pc.p.w)))discard;color=vec4(vec3(.1,.85,.35)*.35,.35);}\n velocity=vec4(8);ids=vec4(9);')
 for name,text in [('fullscreen.vert',v),('coverage.frag',f)]:
  p=b/name;p.write_text(text);run('compile-'+name,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',p,'-o',b/'shaders'/(name+'.spv')]);run('validate-'+name,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',b/'shaders'/(name+'.spv')])
 s=(BASE/'main.cpp').read_text();s=replace(s,'const char*names[]={"A","B","B-no-shadow","B-stale-label"};for(int i=0;i<4;i++)','const char*names[]={"A","B","B-no-shadow","B-stale-label","B-no-rect","B-no-circle","B-no-rotated","B-filled-hole","B-butt","B-same-evenodd","B-same-nonzero","B-opposite-evenodd"};for(int i=0;i<12;i++)');s=replace(s,'s.stale=i==3;auto r=', 's.stale=i==3;s.vectorMode=i>=4?i-3:0;auto r=');(b/'combined-main.cpp').write_text(s)
 run('compile-combined',['g++','-std=c++17','-O2','-I'+str(b),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',b/'combined-main.cpp','-l:libvulkan.so.1','-o',b/'combined'])
