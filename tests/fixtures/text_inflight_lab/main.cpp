// SPDX-License-Identifier: MIT
// Real timeline-gated transfer consumers; no graphics or multi-queue claim.
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#define VK(call) do {VkResult r=(call);if(r!=VK_SUCCESS)throw std::runtime_error(std::string(#call)+": "+std::to_string(r));} while(0)
static unsigned diagnostics=0;
static VKAPI_ATTR VkBool32 VKAPI_CALL debug(VkDebugUtilsMessageSeverityFlagBitsEXT,VkDebugUtilsMessageTypeFlagsEXT,const VkDebugUtilsMessengerCallbackDataEXT* data,void*){diagnostics++;std::cerr<<"VALIDATION: "<<data->pMessage<<'\n';return VK_FALSE;}
struct Buffer {VkBuffer handle{};VkDeviceMemory memory{};void* mapped{};};
struct Lab {
 VkInstance instance{};VkDebugUtilsMessengerEXT messenger{};VkPhysicalDevice physical{};VkDevice device{};VkQueue queue{};VkCommandPool pool{};VkPhysicalDeviceMemoryProperties mem{};VkPhysicalDeviceProperties props{};
 VkImage slot{};VkDeviceMemory imageMemory{};VkSemaphore gate{},ready{},done{};bool validation=false;uint32_t family=0;std::vector<Buffer> buffers;std::vector<VkCommandBuffer> commands;std::vector<VkFence> submissionFences;
 static constexpr uint32_t W=32,H=24,N=W*H;
 Lab(){
  VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.pApplicationName="TEXT18 Inflight Retirement Lab";app.apiVersion=VK_API_VERSION_1_2;
  uint32_t count=0;VK(vkEnumerateInstanceLayerProperties(&count,nullptr));std::vector<VkLayerProperties> layers(count);VK(vkEnumerateInstanceLayerProperties(&count,layers.data()));for(auto& l:layers)validation|=std::string(l.layerName)=="VK_LAYER_KHRONOS_validation";
  const char* layer="VK_LAYER_KHRONOS_validation";const char* ext="VK_EXT_debug_utils";
  VkDebugUtilsMessengerCreateInfoEXT di{VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT};di.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;di.messageType=7;di.pfnUserCallback=debug;
  VkInstanceCreateInfo ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ci.pApplicationInfo=&app;if(validation){ci.enabledLayerCount=1;ci.ppEnabledLayerNames=&layer;ci.enabledExtensionCount=1;ci.ppEnabledExtensionNames=&ext;ci.pNext=&di;}VK(vkCreateInstance(&ci,nullptr,&instance));
  if(validation)VK(reinterpret_cast<PFN_vkCreateDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT"))(instance,&di,nullptr,&messenger));
  VK(vkEnumeratePhysicalDevices(instance,&count,nullptr));std::vector<VkPhysicalDevice> devices(count);VK(vkEnumeratePhysicalDevices(instance,&count,devices.data()));
  for(auto pd:devices){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(pd,&p);if(p.apiVersion<VK_API_VERSION_1_2)continue;VkPhysicalDeviceTimelineSemaphoreFeatures t{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES};VkPhysicalDeviceFeatures2 f{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};f.pNext=&t;vkGetPhysicalDeviceFeatures2(pd,&f);if(!t.timelineSemaphore)continue;uint32_t qn;vkGetPhysicalDeviceQueueFamilyProperties(pd,&qn,nullptr);std::vector<VkQueueFamilyProperties> qp(qn);vkGetPhysicalDeviceQueueFamilyProperties(pd,&qn,qp.data());for(uint32_t q=0;q<qn;q++)if(qp[q].queueFlags&(VK_QUEUE_TRANSFER_BIT|VK_QUEUE_GRAPHICS_BIT|VK_QUEUE_COMPUTE_BIT)){physical=pd;family=q;break;}if(physical)break;}
  if(!physical)throw std::runtime_error("BLOCKED: Vulkan1.2 timeline semaphore transfer path unavailable");
  vkGetPhysicalDeviceProperties(physical,&props);vkGetPhysicalDeviceMemoryProperties(physical,&mem);
  VkFormatProperties fp;vkGetPhysicalDeviceFormatProperties(physical,VK_FORMAT_R32_SFLOAT,&fp);VkFormatFeatureFlags need=VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT;if((fp.optimalTilingFeatures&need)!=need)throw std::runtime_error("BLOCKED: R32 image transfer unsupported");
  float priority=1;VkDeviceQueueCreateInfo q{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};q.queueFamilyIndex=family;q.queueCount=1;q.pQueuePriorities=&priority;
  VkPhysicalDeviceTimelineSemaphoreFeatures enabled{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES};enabled.timelineSemaphore=VK_TRUE;
  VkDeviceCreateInfo dc{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};dc.pNext=&enabled;dc.queueCreateInfoCount=1;dc.pQueueCreateInfos=&q;VK(vkCreateDevice(physical,&dc,nullptr,&device));vkGetDeviceQueue(device,family,0,&queue);
  VkCommandPoolCreateInfo pc{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};pc.queueFamilyIndex=family;pc.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;VK(vkCreateCommandPool(device,&pc,nullptr,&pool));
  VkImageCreateInfo ic{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};ic.imageType=VK_IMAGE_TYPE_2D;ic.format=VK_FORMAT_R32_SFLOAT;ic.extent={W,H,1};ic.mipLevels=ic.arrayLayers=1;ic.samples=VK_SAMPLE_COUNT_1_BIT;ic.tiling=VK_IMAGE_TILING_OPTIMAL;ic.usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT;VK(vkCreateImage(device,&ic,nullptr,&slot));VkMemoryRequirements req;vkGetImageMemoryRequirements(device,slot,&req);VkMemoryAllocateInfo ma{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ma.allocationSize=req.size;ma.memoryTypeIndex=memoryType(req.memoryTypeBits,0);VK(vkAllocateMemory(device,&ma,nullptr,&imageMemory));VK(vkBindImageMemory(device,slot,imageMemory,0));
  gate=timeline();ready=timeline();done=timeline();
  for(int i=0;i<2;i++)buffers.push_back(buffer(VK_BUFFER_USAGE_TRANSFER_SRC_BIT));
  for(int i=0;i<3;i++)buffers.push_back(buffer(VK_BUFFER_USAGE_TRANSFER_DST_BIT));
  std::cout<<"{\"device\":\""<<props.deviceName<<"\",\"driverVersion\":"<<props.driverVersion<<",\"apiVersion\":"<<props.apiVersion<<",\"queue_family\":"<<family<<",\"queue_count\":1,\"timeline_queried_and_enabled\":true,\"validation\":"<<(validation?"true":"false")<<"}\n";
 }
 uint32_t memoryType(uint32_t bits,VkMemoryPropertyFlags need){for(uint32_t i=0;i<mem.memoryTypeCount;i++)if((bits&(1u<<i))&&(mem.memoryTypes[i].propertyFlags&need)==need)return i;throw std::runtime_error("required memory type unavailable");}
 Buffer buffer(VkBufferUsageFlags usage){Buffer b;VkBufferCreateInfo bc{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};bc.size=N*4;bc.usage=usage;VK(vkCreateBuffer(device,&bc,nullptr,&b.handle));VkMemoryRequirements req;vkGetBufferMemoryRequirements(device,b.handle,&req);VkMemoryAllocateInfo a{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};a.allocationSize=req.size;a.memoryTypeIndex=memoryType(req.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);VK(vkAllocateMemory(device,&a,nullptr,&b.memory));VK(vkBindBufferMemory(device,b.handle,b.memory,0));VK(vkMapMemory(device,b.memory,0,N*4,0,&b.mapped));return b;}
 VkSemaphore timeline(){VkSemaphoreTypeCreateInfo t{VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO};t.semaphoreType=VK_SEMAPHORE_TYPE_TIMELINE;t.initialValue=0;VkSemaphoreCreateInfo c{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};c.pNext=&t;VkSemaphore s;VK(vkCreateSemaphore(device,&c,nullptr,&s));return s;}
 VkCommandBuffer start(){VkCommandBufferAllocateInfo a{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};a.commandPool=pool;a.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;a.commandBufferCount=1;VkCommandBuffer cb;VK(vkAllocateCommandBuffers(device,&a,&cb));commands.push_back(cb);VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;VK(vkBeginCommandBuffer(cb,&bi));return cb;}
 void imageBarrier(VkCommandBuffer cb,VkImageLayout old,VkImageLayout next,VkAccessFlags src,VkAccessFlags dst){VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};b.srcAccessMask=src;b.dstAccessMask=dst;b.oldLayout=old;b.newLayout=next;b.srcQueueFamilyIndex=b.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;b.image=slot;b.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,nullptr,0,nullptr,1,&b);}
 VkCommandBuffer producer(int index){auto cb=start();VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};mb.srcAccessMask=VK_ACCESS_HOST_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT;vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_HOST_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,1,&mb,0,nullptr,0,nullptr);
  imageBarrier(cb,index?VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL:VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,index?VK_ACCESS_TRANSFER_READ_BIT:0,VK_ACCESS_TRANSFER_WRITE_BIT);
  VkBufferImageCopy c{};c.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};c.imageExtent={W,H,1};vkCmdCopyBufferToImage(cb,buffers[index].handle,slot,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&c);
  imageBarrier(cb,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT);VK(vkEndCommandBuffer(cb));return cb;}
 VkCommandBuffer consumer(int index){auto cb=start();VkBufferImageCopy c{};c.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};c.imageExtent={W,H,1};vkCmdCopyImageToBuffer(cb,slot,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,buffers[index+2].handle,1,&c);VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};mb.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_HOST_READ_BIT;vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&mb,0,nullptr,0,nullptr);VK(vkEndCommandBuffer(cb));return cb;}
 void submit(VkCommandBuffer cb,std::vector<VkSemaphore> waits,std::vector<uint64_t> values,VkSemaphore signal,uint64_t signalValue){if(waits.size()!=values.size())throw std::runtime_error("wait value count");std::vector<VkPipelineStageFlags> stages(waits.size(),VK_PIPELINE_STAGE_TRANSFER_BIT);VkTimelineSemaphoreSubmitInfo ts{VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO};ts.waitSemaphoreValueCount=values.size();ts.pWaitSemaphoreValues=values.data();ts.signalSemaphoreValueCount=1;ts.pSignalSemaphoreValues=&signalValue;VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.pNext=&ts;si.waitSemaphoreCount=waits.size();si.pWaitSemaphores=waits.data();si.pWaitDstStageMask=stages.data();si.commandBufferCount=1;si.pCommandBuffers=&cb;si.signalSemaphoreCount=1;si.pSignalSemaphores=&signal;VkFenceCreateInfo fc{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VkFence fence;VK(vkCreateFence(device,&fc,nullptr,&fence));VkResult submitted=vkQueueSubmit(queue,1,&si,fence);if(submitted!=VK_SUCCESS){vkDestroyFence(device,fence,nullptr);VK(submitted);}submissionFences.push_back(fence);}
 uint64_t completed(){uint64_t value;VK(vkGetSemaphoreCounterValue(device,done,&value));return value;}
 bool reusable(uint64_t lastConsumer){return completed()>=lastConsumer;}
 void hostGate(uint64_t value){VkSemaphoreSignalInfo s{VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO};s.semaphore=gate;s.value=value;VK(vkSignalSemaphore(device,&s));}
 void waitDone(uint64_t value){VkSemaphoreWaitInfo w{VK_STRUCTURE_TYPE_SEMAPHORE_WAIT_INFO};w.semaphoreCount=1;w.pSemaphores=&done;w.pValues=&value;VK(vkWaitSemaphores(device,&w,10'000'000'000ull));}
 ~Lab(){if(device){uint64_t value=0;vkGetSemaphoreCounterValue(device,gate,&value);if(value<2){VkSemaphoreSignalInfo s{VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO};s.semaphore=gate;s.value=2;vkSignalSemaphore(device,&s);}if(!submissionFences.empty()){
 VkResult finished=vkWaitForFences(device,uint32_t(submissionFences.size()),submissionFences.data(),VK_TRUE,10'000'000'000ull);
 if(finished!=VK_SUCCESS){std::cerr<<"CLEANUP_TIMEOUT_OR_DEVICE_FAILURE: "<<finished<<std::endl;std::_Exit(2);}
 }
 for(auto f:submissionFences)vkDestroyFence(device,f,nullptr);
 for(auto b:buffers){vkUnmapMemory(device,b.memory);vkDestroyBuffer(device,b.handle,nullptr);vkFreeMemory(device,b.memory,nullptr);}for(auto s:{gate,ready,done})if(s)vkDestroySemaphore(device,s,nullptr);vkDestroyImage(device,slot,nullptr);vkFreeMemory(device,imageMemory,nullptr);vkDestroyCommandPool(device,pool,nullptr);vkDestroyDevice(device,nullptr);}if(messenger)reinterpret_cast<PFN_vkDestroyDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT"))(instance,messenger,nullptr);if(instance)vkDestroyInstance(instance,nullptr);}
};
int main(int argc,char** argv){try{
 if(argc!=2 && !(argc==3 && std::string(argv[2])=="--abort-pending"))throw std::runtime_error("usage: inflight_lab NEW_OUTPUT [--abort-pending]");
 std::filesystem::path out=argv[1];if(!std::filesystem::create_directory(out))throw std::runtime_error("Refuse existing output directory");
 {
 Lab v;std::array<std::vector<float>,2> expected;
 for(int generation=0;generation<2;generation++){expected[generation].resize(Lab::N);for(uint32_t i=0;i<Lab::N;i++)expected[generation][i]=float(generation+1)*.25f+float(i%17)/1024;std::memcpy(v.buffers[generation].mapped,expected[generation].data(),Lab::N*4);}
 auto upload0=v.producer(0),a=v.consumer(0),b=v.consumer(1);
 // All three submits are in-flight before releasing the first gate. They use
 // one queue; multiple pending consumers are not parallel hardware execution.
 v.submit(upload0,{v.gate},{1},v.ready,1);v.submit(a,{v.ready},{1},v.done,1);v.submit(b,{v.gate,v.done},{2,1},v.done,2);
 if(argc==3)throw std::runtime_error("INTENTIONAL_ABORT_WITH_PENDING_SUBMISSIONS");
 std::ofstream events(out/"retirement.jsonl");
 auto record=[&](const char* phase,uint64_t expectedValue,bool shouldReuse){auto actual=v.completed();bool reuse=v.reusable(2);events<<"{\"phase\":\""<<phase<<"\",\"completed\":"<<actual<<",\"last_consumer\":2,\"reuse_allowed\":"<<(reuse?"true":"false")<<"}\n";if(actual!=expectedValue||reuse!=shouldReuse)throw std::runtime_error("retirement guard mismatch");};
 record("both_consumers_pending",0,false);v.hostGate(1);v.waitDone(1);record("consumer_A_done_B_pending",1,false);v.hostGate(2);v.waitDone(2);record("both_consumers_done",2,true);
 auto check=[&](int readback,int generation){auto* p=static_cast<float*>(v.buffers[readback+2].mapped);float worst=0;for(uint32_t i=0;i<Lab::N;i++){if(!std::isfinite(p[i]))throw std::runtime_error("nonfinite readback");worst=std::max(worst,std::abs(p[i]-expected[generation][i]));}if(worst!=0)throw std::runtime_error("wrong slot generation");std::ofstream raw(out/("consumer-"+std::to_string(readback)+".r32f"),std::ios::binary);raw.write(reinterpret_cast<char*>(p),Lab::N*4);return worst;};
 check(0,0);check(1,0);
 // Actual counter guard owns permission to record/write the second generation.
 if(!v.reusable(2))throw std::runtime_error("slot not retired");
 auto upload1=v.producer(1),c=v.consumer(2);v.submit(upload1,{v.done},{2},v.ready,2);v.submit(c,{v.ready},{2},v.done,3);v.waitDone(3);check(2,1);
 // Older readbacks remain immutable and still identify generation zero.
 check(0,0);check(1,0);
 std::ofstream summary(out/"numerics.json");summary<<"{\"status\":\"PASS\",\"size\":[32,24],\"queue_count\":1,\"consumer_count\":3,\"generations\":2,\"first_generation_last_consumer\":2,\"final_counter\":"<<v.completed()<<",\"max_readback_error\":0,\"validation_enabled\":"<<(v.validation?"true":"false")<<",\"parallel_hardware_claimed\":false}\n";
 }
 if(diagnostics)throw std::runtime_error("validation diagnostics");
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
