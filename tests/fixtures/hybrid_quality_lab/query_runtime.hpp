// SPDX-License-Identifier: MIT
// Small conditional companion, shares Engine Scale Lab's physical-device choice.
// Dedicated device enables only BDA/AS/query, never a ray tracing pipeline/SBT.
struct QueryRuntime {
 VkDevice d{};VkPhysicalDevice pd{};VkQueue queue{};VkCommandPool pool{};VkCommandBuffer cb{};VkFence fence{};
 VkDescriptorSetLayout dsl{};VkDescriptorPool dp{};VkPipelineLayout pl{};VkPipeline pipeline{};
 VkPhysicalDeviceMemoryProperties mem{};VkPhysicalDeviceAccelerationStructurePropertiesKHR props{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_PROPERTIES_KHR};
 std::vector<Buffer> buffers;std::vector<VkAccelerationStructureKHR> structures;
 PFN_vkCreateAccelerationStructureKHR createAS{};PFN_vkDestroyAccelerationStructureKHR destroyAS{};PFN_vkGetAccelerationStructureBuildSizesKHR sizesAS{};PFN_vkCmdBuildAccelerationStructuresKHR buildAS{};PFN_vkGetAccelerationStructureDeviceAddressKHR addressAS{};
 QueryRuntime(Vulkan&v):pd(v.physical),mem(v.mem){
  float priority=1;VkDeviceQueueCreateInfo qi{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};qi.queueFamilyIndex=v.family;qi.queueCount=1;qi.pQueuePriorities=&priority;
  VkPhysicalDeviceRayQueryFeaturesKHR rq{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_QUERY_FEATURES_KHR};rq.rayQuery=VK_TRUE;
  VkPhysicalDeviceAccelerationStructureFeaturesKHR as{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_FEATURES_KHR};as.accelerationStructure=VK_TRUE;as.pNext=&rq;
  VkPhysicalDeviceVulkan12Features f{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};f.bufferDeviceAddress=VK_TRUE;f.pNext=&as;
  const char*ext[]={VK_KHR_ACCELERATION_STRUCTURE_EXTENSION_NAME,VK_KHR_RAY_QUERY_EXTENSION_NAME,VK_KHR_DEFERRED_HOST_OPERATIONS_EXTENSION_NAME};
  VkDeviceCreateInfo ci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};ci.pNext=&f;ci.queueCreateInfoCount=1;ci.pQueueCreateInfos=&qi;ci.enabledExtensionCount=3;ci.ppEnabledExtensionNames=ext;VK(vkCreateDevice(pd,&ci,nullptr,&d));vkGetDeviceQueue(d,v.family,0,&queue);
#define LOAD_AS(field,name) field=reinterpret_cast<PFN_##name>(vkGetDeviceProcAddr(d,#name));if(!field)throw std::runtime_error("Missing " #name)
  LOAD_AS(createAS,vkCreateAccelerationStructureKHR);LOAD_AS(destroyAS,vkDestroyAccelerationStructureKHR);LOAD_AS(sizesAS,vkGetAccelerationStructureBuildSizesKHR);LOAD_AS(buildAS,vkCmdBuildAccelerationStructuresKHR);LOAD_AS(addressAS,vkGetAccelerationStructureDeviceAddressKHR);
#undef LOAD_AS
  VkPhysicalDeviceProperties2 properties{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2};properties.pNext=&props;vkGetPhysicalDeviceProperties2(pd,&properties);
  VkCommandPoolCreateInfo pc{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};pc.queueFamilyIndex=v.family;pc.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;VK(vkCreateCommandPool(d,&pc,nullptr,&pool));
  VkCommandBufferAllocateInfo ca{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};ca.commandPool=pool;ca.commandBufferCount=1;ca.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;VK(vkAllocateCommandBuffers(d,&ca,&cb));VkFenceCreateInfo fc{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VK(vkCreateFence(d,&fc,nullptr,&fence));
 }
 Buffer alloc(VkDeviceSize bytes,VkBufferUsageFlags usage,bool address=true){
  Buffer b;b.size=bytes;VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};ci.size=bytes;ci.usage=usage|(address?VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT:0);VK(vkCreateBuffer(d,&ci,nullptr,&b.buffer));VkMemoryRequirements req;vkGetBufferMemoryRequirements(d,b.buffer,&req);
  uint32_t type=0;while(type<mem.memoryTypeCount&&(!(req.memoryTypeBits&(1u<<type))||(mem.memoryTypes[type].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))!=(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)))type++;
  if(type==mem.memoryTypeCount)throw std::runtime_error("Query fixture requires coherent host-visible allocation");
  VkMemoryAllocateFlagsInfo flags{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO};flags.flags=VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT;VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=req.size;ai.memoryTypeIndex=type;ai.pNext=address?&flags:nullptr;VK(vkAllocateMemory(d,&ai,nullptr,&b.memory));VK(vkBindBufferMemory(d,b.buffer,b.memory,0));VK(vkMapMemory(d,b.memory,0,bytes,0,&b.map));buffers.push_back(b);return b;
 }
 VkDeviceAddress addr(Buffer b){VkBufferDeviceAddressInfo ai{VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO};ai.buffer=b.buffer;return vkGetBufferDeviceAddress(d,&ai);}
 void begin(){VK(vkResetCommandBuffer(cb,0));VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;VK(vkBeginCommandBuffer(cb,&bi));}
 void finish(){VK(vkEndCommandBuffer(cb));VK(vkResetFences(d,1,&fence));VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.commandBufferCount=1;si.pCommandBuffers=&cb;VK(vkQueueSubmit(queue,1,&si,fence));VK(vkWaitForFences(d,1,&fence,VK_TRUE,30'000'000'000ull));}
 void barrier(VkPipelineStageFlags src,VkAccessFlags sa,VkPipelineStageFlags dst,VkAccessFlags da){VkMemoryBarrier b{VK_STRUCTURE_TYPE_MEMORY_BARRIER};b.srcAccessMask=sa;b.dstAccessMask=da;vkCmdPipelineBarrier(cb,src,dst,0,1,&b,0,nullptr,0,nullptr);}
 VkAccelerationStructureKHR build(VkAccelerationStructureGeometryKHR geometry,uint32_t count,VkAccelerationStructureTypeKHR type){
  VkAccelerationStructureBuildGeometryInfoKHR info{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_BUILD_GEOMETRY_INFO_KHR};info.type=type;info.flags=VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR;info.mode=VK_BUILD_ACCELERATION_STRUCTURE_MODE_BUILD_KHR;info.geometryCount=1;info.pGeometries=&geometry;
  VkAccelerationStructureBuildSizesInfoKHR sizes{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_BUILD_SIZES_INFO_KHR};sizesAS(d,VK_ACCELERATION_STRUCTURE_BUILD_TYPE_DEVICE_KHR,&info,&count,&sizes);
  Buffer storage=alloc(sizes.accelerationStructureSize,VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_STORAGE_BIT_KHR);VkAccelerationStructureCreateInfoKHR ci{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_CREATE_INFO_KHR};ci.buffer=storage.buffer;ci.size=sizes.accelerationStructureSize;ci.type=type;VkAccelerationStructureKHR as;VK(createAS(d,&ci,nullptr,&as));structures.push_back(as);
  uint64_t alignment=props.minAccelerationStructureScratchOffsetAlignment;Buffer scratch=alloc(sizes.buildScratchSize+alignment-1,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);uint64_t scratchAddress=(addr(scratch)+alignment-1)&~(alignment-1);info.scratchData.deviceAddress=scratchAddress;info.dstAccelerationStructure=as;
  VkAccelerationStructureBuildRangeInfoKHR range{};range.primitiveCount=count;const auto*rangePtr=&range;buildAS(cb,1,&info,&rangePtr);
  std::cout<<"{\"as_type\":"<<type<<",\"as_bytes\":"<<sizes.accelerationStructureSize<<",\"scratch_bytes\":"<<sizes.buildScratchSize<<",\"scratch_alignment\":"<<alignment<<"}\n";return as;
 }
 void run(const std::string&shaderDir,const std::filesystem::path&out){
  // Same three rectangles/alpha strips as raster initial frame, in world space.
  float vertices[18][3];float centers[3][2]={{-.25,0},{.2,.15},{.82,-.25}},extents[3][2]={{.18,.25},{.22,.4},{.12,.2}},depths[3]={.6,.35,.2};int corners[6][2]={{-1,-1},{1,-1},{1,1},{-1,-1},{1,1},{-1,1}};
  for(int j=0;j<3;j++)for(int k=0;k<6;k++){vertices[j*6+k][0]=centers[j][0]+corners[k][0]*extents[j][0];vertices[j*6+k][1]=centers[j][1]+corners[k][1]*extents[j][1];vertices[j*6+k][2]=depths[j];}
  Buffer verts=alloc(sizeof(vertices),VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR);std::memcpy(verts.map,vertices,sizeof(vertices));
  VkAccelerationStructureGeometryKHR geo{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_KHR};geo.geometryType=VK_GEOMETRY_TYPE_TRIANGLES_KHR;auto&tri=geo.geometry.triangles;tri.sType=VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_TRIANGLES_DATA_KHR;tri.vertexFormat=VK_FORMAT_R32G32B32_SFLOAT;tri.vertexData.deviceAddress=addr(verts);tri.vertexStride=12;tri.maxVertex=17;tri.indexType=VK_INDEX_TYPE_NONE_KHR;
  begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_KHR,VK_ACCESS_SHADER_READ_BIT);
  auto blas=build(geo,6,VK_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL_KHR);
  // Query address while object exists; contents become valid after build finishes.
  VkAccelerationStructureDeviceAddressInfoKHR ai{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_DEVICE_ADDRESS_INFO_KHR};ai.accelerationStructure=blas;
  VkAccelerationStructureInstanceKHR inst{};inst.transform.matrix[0][0]=inst.transform.matrix[1][1]=inst.transform.matrix[2][2]=1;inst.mask=255;inst.accelerationStructureReference=addressAS(d,&ai);
  Buffer instances=alloc(sizeof(inst),VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR);std::memcpy(instances.map,&inst,sizeof(inst));
  barrier(VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_KHR|VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_ACCELERATION_STRUCTURE_WRITE_BIT_KHR|VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_KHR,VK_ACCESS_ACCELERATION_STRUCTURE_READ_BIT_KHR|VK_ACCESS_SHADER_READ_BIT);
  VkAccelerationStructureGeometryKHR top{VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_KHR};top.geometryType=VK_GEOMETRY_TYPE_INSTANCES_KHR;top.geometry.instances.sType=VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_INSTANCES_DATA_KHR;top.geometry.instances.data.deviceAddress=addr(instances);
  auto tlas=build(top,1,VK_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL_KHR);
  barrier(VK_PIPELINE_STAGE_ACCELERATION_STRUCTURE_BUILD_BIT_KHR,VK_ACCESS_ACCELERATION_STRUCTURE_WRITE_BIT_KHR,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_ACCELERATION_STRUCTURE_READ_BIT_KHR);finish();
  VkDescriptorSetLayoutBinding bindings[2]{};bindings[0]={0,VK_DESCRIPTOR_TYPE_ACCELERATION_STRUCTURE_KHR,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr};bindings[1]={1,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1,VK_SHADER_STAGE_COMPUTE_BIT,nullptr};VkDescriptorSetLayoutCreateInfo dl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};dl.bindingCount=2;dl.pBindings=bindings;VK(vkCreateDescriptorSetLayout(d,&dl,nullptr,&dsl));
  VkPushConstantRange pc{VK_SHADER_STAGE_COMPUTE_BIT,0,16};VkPipelineLayoutCreateInfo plc{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};plc.setLayoutCount=1;plc.pSetLayouts=&dsl;plc.pushConstantRangeCount=1;plc.pPushConstantRanges=&pc;VK(vkCreatePipelineLayout(d,&plc,nullptr,&pl));
  VkDescriptorPoolSize poolSizes[2]={{VK_DESCRIPTOR_TYPE_ACCELERATION_STRUCTURE_KHR,1},{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1}};VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dpi.maxSets=1;dpi.poolSizeCount=2;dpi.pPoolSizes=poolSizes;VK(vkCreateDescriptorPool(d,&dpi,nullptr,&dp));VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};dai.descriptorPool=dp;dai.descriptorSetCount=1;dai.pSetLayouts=&dsl;VkDescriptorSet set;VK(vkAllocateDescriptorSets(d,&dai,&set));
  Buffer result=alloc(65*49*16,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,false);VkDescriptorBufferInfo bi{result.buffer,0,result.size};VkWriteDescriptorSetAccelerationStructureKHR asi{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET_ACCELERATION_STRUCTURE_KHR};asi.accelerationStructureCount=1;asi.pAccelerationStructures=&tlas;VkWriteDescriptorSet writes[2]{};for(auto&w:writes){w.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;w.dstSet=set;w.descriptorCount=1;}writes[0].descriptorType=VK_DESCRIPTOR_TYPE_ACCELERATION_STRUCTURE_KHR;writes[0].pNext=&asi;writes[1].dstBinding=1;writes[1].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;writes[1].pBufferInfo=&bi;vkUpdateDescriptorSets(d,2,writes,0,nullptr);
  std::ifstream file(shaderDir+"/query.comp.spv",std::ios::binary|std::ios::ate);if(!file)throw std::runtime_error("Missing query shader");size_t bytes=file.tellg();std::vector<uint32_t> code(bytes/4);file.seekg(0);file.read((char*)code.data(),bytes);VkShaderModuleCreateInfo sci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};sci.codeSize=bytes;sci.pCode=code.data();VkShaderModule sm;VK(vkCreateShaderModule(d,&sci,nullptr,&sm));VkComputePipelineCreateInfo pi{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};pi.layout=pl;pi.stage={VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};pi.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;pi.stage.module=sm;pi.stage.pName="main";VkResult created=vkCreateComputePipelines(d,VK_NULL_HANDLE,1,&pi,nullptr,&pipeline);vkDestroyShaderModule(d,sm,nullptr);VK(created);
  for(uint32_t reflection=0;reflection<2;reflection++){
   struct {uint32_t count,reflection;float scale,light;}p{65*49,reflection,1.f,-.35f};begin();vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_COMPUTE,pl,0,1,&set,0,nullptr);vkCmdPushConstants(cb,pl,VK_SHADER_STAGE_COMPUTE_BIT,0,16,&p);vkCmdDispatch(cb,(65*49+63)/64,1,1);barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);finish();
   auto data=(float*)result.map;uint32_t hit=0,miss=0;for(uint32_t i=0;i<65*49;i++){for(int c=0;c<4;c++)if(!std::isfinite(data[i*4+c]))throw std::runtime_error("Query nonfinite output");bool h=reflection?data[i*4+3]>0:data[i*4]<.5;hit+=h;miss+=!h;}if(!hit||!miss)throw std::runtime_error("Query hit/miss coverage missing");
   // Independent CPU ray-plane/rectangle oracle, including cutout UV and nearest
   // accepted intersection. This is correctness evidence, not GPU performance.
   uint32_t mismatches=0;
   for(uint32_t i=0;i<65*49;i++){
    float ox=(float(i%65)+.5f)/65.f*1.3f-.65f,oy=(float(i/65)+.5f)/49.f*2.f-1.f,oz=oy>.45f?.65f:.8f;
    int nearest=-1;float nearestT=100.f;
    for(int material=0;material<3;material++){
     float t=oz-depths[material],x=ox+t*(reflection?.413f:.35f),y=oy;
     if(t<=.001f || std::abs(x-centers[material][0])>extents[material][0] || std::abs(y-centers[material][1])>extents[material][1])continue;
     float u=(x-centers[material][0])/extents[material][0]*.5f+.5f;
     if(material==1 && (u*7.f-std::floor(u*7.f))>.5f)continue;
     if(t<nearestT){nearest=material;nearestT=t;}
    }
    const float materialColors[3][3]={{.3f,.4f,.5f},{.2f,.6f,.1f},{.7f,.2f,.1f}};
    const float missColor[4]={.08f,.12f,.2f,0.f};
    for(int c=0;c<4;c++){
     float expected=reflection?(nearest<0?missColor[c]:(c==3?1.f:materialColors[nearest][c])):(nearest<0?1.f:0.f);
     if(!std::isfinite(expected)||!std::isfinite(data[4*i+c])||std::abs(data[4*i+c]-expected)>1e-5f)mismatches++;
    }
   }
   if(mismatches)throw std::runtime_error("Query CPU oracle mismatch: "+std::to_string(mismatches));
   std::string name=reflection?"query-reflection":"query-shadow";pgm(out/(name+".pgm"),data,65,49,4);std::ofstream binary(out/(name+".rgba32f"),std::ios::binary);binary.write((char*)result.map,result.size);std::cout<<"{\"query_mode\":\""<<name<<"\",\"hit_pixels\":"<<hit<<",\"miss_pixels\":"<<miss<<",\"oracle_mismatches\":0,\"execution\":\"PASS\"}\n";
  }
 }
 ~QueryRuntime(){if(!d)return;vkDeviceWaitIdle(d);if(pipeline)vkDestroyPipeline(d,pipeline,nullptr);if(pl)vkDestroyPipelineLayout(d,pl,nullptr);if(dp)vkDestroyDescriptorPool(d,dp,nullptr);if(dsl)vkDestroyDescriptorSetLayout(d,dsl,nullptr);for(auto as:structures)destroyAS(d,as,nullptr);for(auto b:buffers){vkUnmapMemory(d,b.memory);vkDestroyBuffer(d,b.buffer,nullptr);vkFreeMemory(d,b.memory,nullptr);}vkDestroyFence(d,fence,nullptr);vkDestroyCommandPool(d,pool,nullptr);vkDestroyDevice(d,nullptr);}
};
