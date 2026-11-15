import os
from pathlib import Path
HERE=Path(__file__).resolve().parent
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('hook count '+a)
 return s.replace(a,b)
def build(out,run):
 run('prepare',[os.sys.executable,HERE.parent/'text_active_mrt_lab/run_lab.py','--out',out/'prepared'])
 b=out/'prepared/build';s=(b/'active_lab_reused.hpp').read_text()
 s=replace(s,'Image depth;size_t readDepth;','Image depth;size_t readDepth;size_t sceneVB=0,casterVB=0;uint32_t casterCount=0;VkDescriptorSet labelSet{};VkPipeline labelPipeline{};float cameraX=0,cameraY=0;bool bypass=false,stale=false;')
 s=replace(s,'VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT,0,16}','VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,0,16}')
 s=replace(s,'VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};','VkVertexInputBindingDescription vbind{0,24,VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription attr{0,0,VK_FORMAT_R32G32B32_SFLOAT,0};VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&vbind;vi.vertexAttributeDescriptionCount=1;vi.pVertexAttributeDescriptions=&attr;')
 s=replace(s,'ds.depthWriteEnable=gBadDepth;ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;','ds.depthWriteEnable=VK_TRUE;ds.depthCompareOp=VK_COMPARE_OP_LESS;')
 s=replace(s,'vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);','VK(result);ds.depthWriteEnable=VK_FALSE;VK(vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&labelPipeline));vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);')
 s=replace(s,'VkClearDepthStencilValue dv{.375f,0}','VkClearDepthStencilValue dv{1.f,0}')
 old='float rgba[]={ink[0],ink[1],ink[2],ink[3]};vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,rgba);vkCmdDraw(cb,3,1,0,0);'
 new='''VkDeviceSize zero=0;auto emit=[&](size_t v,uint32_t first,uint32_t count,int kind){float p[]={cameraX,cameraY,float(kind),bypass?1.f:0.f};if(kind==3&&stale){p[0]=.25f;p[1]=.125f;}vkCmdBindVertexBuffers(cb,0,1,&buffers[v].buffer,&zero);vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,16,p);vkCmdDraw(cb,count,1,first,0);};emit(sceneVB,0,6,0);emit(casterVB,0,casterCount,1);emit(sceneVB,6,6,2);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,labelPipeline);vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textLayout,0,1,&labelSet,0,nullptr);emit(sceneVB,12,6,3);'''
 s=replace(s,old,new);s=replace(s,'vkDestroyPipeline(device,textPipeline,nullptr);','vkDestroyPipeline(device,labelPipeline,nullptr);vkDestroyPipeline(device,textPipeline,nullptr);')
 (b/'active_lab_reused.hpp').write_text(s)
 (b/'shadow_reused.hpp').write_text(replace((HERE.parent/'text_shadow_lab/main.cpp').read_text(),'int main(int argc,char**argv)','int unused_shadow_main(int argc,char**argv)'))
 for src,dest in [(HERE/'world.vert','fullscreen.vert'),(HERE/'world.frag','coverage.frag'),(HERE.parent/'text_shadow_lab/shadow.vert','shadow.vert')]:
  run('compile-'+dest,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',src,'-o',b/'shaders'/(dest+'.spv')]);run('validate-'+dest,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',b/'shaders'/(dest+'.spv')])
 run('compile-scene',['g++','-std=c++17','-O2','-I'+str(b),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',b/'scene'])
 return b
