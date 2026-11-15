// SPDX-License-Identifier: MIT
// Real offscreen Vulkan integration; synthetic coverage only, not a font engine.
#define main engine_scale_lab_original_main
#include "../engine_scale_lab/main.cpp"
#undef main
#include <iomanip>

struct TextLab: Vulkan {
  Image target, velocity, ids, coverage;
  VkDescriptorSetLayout textSetLayout{};
  VkDescriptorPool textPool{};
  VkDescriptorSet textSet{};
  VkPipelineLayout textLayout{};
  VkRenderPass textPass{};
  VkFramebuffer textFramebuffer{};
  VkPipeline textPipeline{};
  size_t upload,readColor,readVelocity,readIds;
  TextLab(const std::string& dir): Vulkan(65*49,dir,true) {
    VkFormatProperties props{};
    vkGetPhysicalDeviceFormatProperties(physical,VK_FORMAT_R32G32B32A32_SFLOAT,&props);
    VkFormatFeatureFlags needed=VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT|VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
    if((props.optimalTilingFeatures&needed)!=needed)throw std::runtime_error("BLOCKED: RGBA32F attachment/blend/transfer unavailable");
    vkGetPhysicalDeviceFormatProperties(physical,VK_FORMAT_R32_SFLOAT,&props);
    VkFormatFeatureFlags maskNeeded=VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
    if((props.optimalTilingFeatures&maskNeeded)!=maskNeeded)throw std::runtime_error("BLOCKED: R32_SFLOAT sampling/transfer unavailable");
    // Inherited sampler is nearest/no anisotropy/no compare: no linear-filter
    // capability is assumed. A linear path must query its separate format bit.
    if(properties.limits.maxColorAttachments<3)throw std::runtime_error("BLOCKED: three color slots unavailable");
    auto usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    target=image(VK_FORMAT_R32G32B32A32_SFLOAT,usage,VK_IMAGE_ASPECT_COLOR_BIT);
    velocity=image(VK_FORMAT_R32G32B32A32_SFLOAT,usage,VK_IMAGE_ASPECT_COLOR_BIT);
    ids=image(VK_FORMAT_R32G32B32A32_SFLOAT,usage,VK_IMAGE_ASPECT_COLOR_BIT);
    coverage=image(VK_FORMAT_R32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
    upload=buffers.size();buffers.push_back(buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT));
    readColor=buffers.size();buffers.push_back(buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    readVelocity=buffers.size();buffers.push_back(buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    readIds=buffers.size();buffers.push_back(buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    VkDescriptorSetLayoutBinding binding{0,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr};
    VkDescriptorSetLayoutCreateInfo sl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};sl.bindingCount=1;sl.pBindings=&binding;VK(vkCreateDescriptorSetLayout(device,&sl,nullptr,&textSetLayout));
    VkPushConstantRange range{VK_SHADER_STAGE_FRAGMENT_BIT,0,16};
    VkPipelineLayoutCreateInfo pl{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pl.setLayoutCount=1;pl.pSetLayouts=&textSetLayout;pl.pushConstantRangeCount=1;pl.pPushConstantRanges=&range;VK(vkCreatePipelineLayout(device,&pl,nullptr,&textLayout));
    VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};
    VkDescriptorPoolCreateInfo dp{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dp.maxSets=1;dp.poolSizeCount=1;dp.pPoolSizes=&size;VK(vkCreateDescriptorPool(device,&dp,nullptr,&textPool));
    VkDescriptorSetAllocateInfo sa{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};sa.descriptorPool=textPool;sa.descriptorSetCount=1;sa.pSetLayouts=&textSetLayout;VK(vkAllocateDescriptorSets(device,&sa,&textSet));
    VkDescriptorImageInfo imageInfo{sampler,coverage.view,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};write.dstSet=textSet;write.descriptorCount=1;write.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;write.pImageInfo=&imageInfo;vkUpdateDescriptorSets(device,1,&write,0,nullptr);
    VkAttachmentDescription attachments[3]{};
    for(auto& a:attachments){a.format=VK_FORMAT_R32G32B32A32_SFLOAT;a.samples=VK_SAMPLE_COUNT_1_BIT;a.loadOp=VK_ATTACHMENT_LOAD_OP_LOAD;a.storeOp=VK_ATTACHMENT_STORE_OP_STORE;a.stencilLoadOp=VK_ATTACHMENT_LOAD_OP_DONT_CARE;a.stencilStoreOp=VK_ATTACHMENT_STORE_OP_DONT_CARE;a.initialLayout=a.finalLayout=VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;}
    // Separate overlay fallback: three slots retained, non-target refs unused and
    // preserved. No independentBlend assumption or forged one-attachment pipeline.
    VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}};
    uint32_t preserved[]={1,2};
    VkSubpassDescription sub{};sub.pipelineBindPoint=VK_PIPELINE_BIND_POINT_GRAPHICS;sub.colorAttachmentCount=3;sub.pColorAttachments=refs;sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;
    VkRenderPassCreateInfo rp{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};rp.attachmentCount=3;rp.pAttachments=attachments;rp.subpassCount=1;rp.pSubpasses=&sub;VK(vkCreateRenderPass(device,&rp,nullptr,&textPass));
    VkImageView views[]={target.view,velocity.view,ids.view};
    VkFramebufferCreateInfo fb{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};fb.renderPass=textPass;fb.attachmentCount=3;fb.pAttachments=views;fb.width=width;fb.height=height;fb.layers=1;VK(vkCreateFramebuffer(device,&fb,nullptr,&textFramebuffer));
    auto vs=shader("fullscreen.vert"),fs=shader("coverage.frag");
    VkPipelineShaderStageCreateInfo stages[2]{};for(int i=0;i<2;i++){stages[i]={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};stages[i].stage=i?VK_SHADER_STAGE_FRAGMENT_BIT:VK_SHADER_STAGE_VERTEX_BIT;stages[i].module=i?fs:vs;stages[i].pName="main";}
    VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};ia.topology=VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkViewport viewport{0,0,float(width),float(height),0,1};VkRect2D rect{{0,0},{width,height}};
    VkPipelineViewportStateCreateInfo vp{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};vp.viewportCount=vp.scissorCount=1;vp.pViewports=&viewport;vp.pScissors=&rect;
    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};rs.polygonMode=VK_POLYGON_MODE_FILL;rs.cullMode=VK_CULL_MODE_NONE;rs.lineWidth=1;
    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};ms.rasterizationSamples=VK_SAMPLE_COUNT_1_BIT;
    VkPipelineColorBlendAttachmentState blends[3]{};for(auto& a:blends){a.colorWriteMask=15;a.blendEnable=VK_TRUE;a.srcColorBlendFactor=a.srcAlphaBlendFactor=VK_BLEND_FACTOR_ONE;a.dstColorBlendFactor=a.dstAlphaBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;a.colorBlendOp=a.alphaBlendOp=VK_BLEND_OP_ADD;}
    VkPipelineColorBlendStateCreateInfo bs{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};bs.attachmentCount=3;bs.pAttachments=blends;
    VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};pi.stageCount=2;pi.pStages=stages;pi.pVertexInputState=&vi;pi.pInputAssemblyState=&ia;pi.pViewportState=&vp;pi.pRasterizationState=&rs;pi.pMultisampleState=&ms;pi.pColorBlendState=&bs;pi.layout=textLayout;pi.renderPass=textPass;
    auto result=vkCreateGraphicsPipelines(device,pipelineCache,1,&pi,nullptr,&textPipeline);vkDestroyShaderModule(device,vs,nullptr);vkDestroyShaderModule(device,fs,nullptr);VK(result);
  }
  std::array<std::vector<float>,3> draw(const std::vector<float>& mask){
    if(mask.size()!=width*height)throw std::runtime_error("invalid mask dimensions");
    for(float x:mask)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("invalid coverage");
    std::memcpy(buffers[upload].map,mask.data(),mask.size()*4);
    begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);
    transition(coverage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,0,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);
    VkBufferImageCopy copy{};copy.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};copy.imageExtent={width,height,1};vkCmdCopyBufferToImage(cb,buffers[upload].buffer,coverage.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&copy);
    transition(coverage,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
    Image images[]={target,velocity,ids};float clears[3][4]={{.2f,.2f,.2f,1},{.125f,-.25f,.5f,1},{37,91,12,1}};
    VkImageSubresourceRange range{VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
    for(int i=0;i<3;i++){transition(images[i],VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,0,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);VkClearColorValue clear{};std::memcpy(clear.float32,clears[i],16);vkCmdClearColorImage(cb,images[i].image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,&clear,1,&range);transition(images[i],VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_ACCESS_COLOR_ATTACHMENT_READ_BIT|VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);}
    VkRenderPassBeginInfo rp{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};rp.renderPass=textPass;rp.framebuffer=textFramebuffer;rp.renderArea={{0,0},{width,height}};
    vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textPipeline);vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,textLayout,0,1,&textSet,0,nullptr);float rgba[]={1,1,1,.8f};vkCmdPushConstants(cb,textLayout,VK_SHADER_STAGE_FRAGMENT_BIT,0,16,rgba);vkCmdDraw(cb,3,1,0,0);vkCmdEndRenderPass(cb);
    size_t reads[]={readColor,readVelocity,readIds};
    for(int i=0;i<3;i++){transition(images[i],VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT|VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);copyImage(images[i],VK_IMAGE_ASPECT_COLOR_BIT,buffers[reads[i]]);}
    barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);submit();
    std::array<std::vector<float>,3> out;for(int i=0;i<3;i++){out[i].resize(width*height*4);std::memcpy(out[i].data(),buffers[reads[i]].map,out[i].size()*4);}return out;
  }
  ~TextLab(){vkDeviceWaitIdle(device);vkDestroyPipeline(device,textPipeline,nullptr);vkDestroyFramebuffer(device,textFramebuffer,nullptr);vkDestroyRenderPass(device,textPass,nullptr);vkDestroyDescriptorPool(device,textPool,nullptr);vkDestroyPipelineLayout(device,textLayout,nullptr);vkDestroyDescriptorSetLayout(device,textSetLayout,nullptr);for(auto im:{target,velocity,ids,coverage}){vkDestroyImageView(device,im.view,nullptr);vkDestroyImage(device,im.image,nullptr);vkFreeMemory(device,im.memory,nullptr);}}
};
static void save(const std::filesystem::path& p,const std::vector<float>& data){std::ofstream f(p,std::ios::binary);f.write((const char*)data.data(),data.size()*4);if(!f)throw std::runtime_error("write failed");}
int main(int argc,char** argv){try{
  if(argc!=3)throw std::runtime_error("usage: text_vector_lab SHADERS NEW_OUTPUT");
  std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("Refuse existing output directory");
  TextLab lab(argv[1]);std::cout<<"{\"driverVersion\":"<<lab.properties.driverVersion<<",\"vendorID\":"<<lab.properties.vendorID<<",\"deviceID\":"<<lab.properties.deviceID<<"}\n";std::ofstream metrics(out/"metrics.jsonl");
  for(int frame=0;frame<5;frame++){
    std::vector<float> mask(lab.width*lab.height,.5f);
    if(frame){float shift=(frame-1)*.25f;for(unsigned y=0;y<lab.height;y++)for(unsigned x=0;x<lab.width;x++){int samples=0;for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++){float px=x+(sx+.5f)/4-shift,py=y+(sy+.5f)/4;bool outer=px>=12&&px<53&&py>=6&&py<43;bool hole=px>=22&&px<43&&py>=16&&py<33;samples+=outer&&!hole;}mask[y*lab.width+x]=samples/16.f;}}
    auto pixels=lab.draw(mask);double error=0;float sent[2][4]={{.125f,-.25f,.5f,1},{37,91,12,1}};
    for(size_t i=0;i<mask.size();i++){for(int c=0;c<4;c++){double expected=c==3?1:.2+mask[i]*.8*.8;if(!std::isfinite(pixels[0][i*4+c]))throw std::runtime_error("nonfinite GPU color");error=std::max(error,std::abs(pixels[0][i*4+c]-expected));for(int k=0;k<2;k++)if(pixels[k+1][i*4+c]!=sent[k][c])throw std::runtime_error("non-target sentinel changed");}}
    if(error>1e-6)throw std::runtime_error("linear-over reference mismatch");
    auto name=std::string("frame-")+std::to_string(frame);save(out/(name+".coverage32f"),mask);save(out/(name+".rgba32f"),pixels[0]);save(out/(name+".velocity32f"),pixels[1]);save(out/(name+".id32f"),pixels[2]);metrics<<"{\"frame\":"<<frame<<",\"max_error\":"<<std::setprecision(10)<<error<<",\"tolerance\":0.000001,\"sentinels\":\"UNCHANGED\",\"status\":\"PASS\"}\n";
  }
  if(validationErrors)throw std::runtime_error("validation errors");
  std::cout<<"TEXT18_GPU_PASS validation_enabled="<<lab.validation<<" frames=5\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
