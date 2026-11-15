/* Original controlled lifetime fault injection, software Vulkan only.
 * Timeline wait ensures the ordinary descriptor set is pending without races. */
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned errors, expected;
static const char *expected_id="VUID-vkUpdateDescriptorSets-None-03047";
static const char *phase="setup";
static VKAPI_ATTR VkBool32 VKAPI_CALL cb(VkDebugUtilsMessageSeverityFlagBitsEXT severity,VkDebugUtilsMessageTypeFlagsEXT type,const VkDebugUtilsMessengerCallbackDataEXT *d,void *u){
 (void)type;(void)u;
 if(!(severity&VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT))return VK_FALSE;
 errors++;if(d->pMessageIdName&&!strcmp(d->pMessageIdName,expected_id))expected++;
 fprintf(stderr,"VUID phase=%s id=%s\n",phase,d->pMessageIdName?d->pMessageIdName:"null");
 return VK_TRUE; /* Abort the deliberately invalid update before it reaches ICD. */
}
#define CHECK(call) do {VkResult result=(call);if(result!=VK_SUCCESS){fprintf(stderr,"FAIL %s: %d\n",#call,result);goto cleanup;}}while(0)
static void record(VkCommandBuffer cmd,VkPipeline pipeline,VkPipelineLayout layout,VkDescriptorSet set,VkBuffer out){
 vkCmdBindPipeline(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
 vkCmdBindDescriptorSets(cmd,VK_PIPELINE_BIND_POINT_COMPUTE,layout,0,1,&set,0,NULL);
 vkCmdDispatch(cmd,1,1,1);
 VkBufferMemoryBarrier b={.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT,.dstAccessMask=VK_ACCESS_HOST_READ_BIT,.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.buffer=out,.offset=0,.size=16};
 vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,0,NULL,1,&b,0,NULL);
}
int main(int argc,char **argv){
 if(argc!=3||(strcmp(argv[1],"good")&&strcmp(argv[1],"bad")&&strcmp(argv[1],"wrong-output")&&strcmp(argv[1],"pending-reset")&&strcmp(argv[1],"stale-submit")))return 64;
 int bad=!strcmp(argv[1],"bad"),wrong=!strcmp(argv[1],"wrong-output"),resetPending=!strcmp(argv[1],"pending-reset"),stale=!strcmp(argv[1],"stale-submit"),rc=2,pending=0;
 unsigned expectedErrors=(bad||resetPending||stale)?1u:0u;
 if(resetPending)expected_id="VUID-vkResetCommandBuffer-commandBuffer-00045";
 if(stale)expected_id="VUID-vkQueueSubmit-pCommandBuffers-00070";
 VkResult rejectedCall=VK_SUCCESS;
 VkInstance instance=VK_NULL_HANDLE;VkDevice device=VK_NULL_HANDLE;VkDebugUtilsMessengerEXT messenger=VK_NULL_HANDLE;
 PFN_vkDestroyDebugUtilsMessengerEXT destroy=NULL;
 VkBuffer buffers[3]={0};VkDeviceMemory memory[3]={0};void *mapped[3]={0};
 VkShaderModule shader=VK_NULL_HANDLE;VkDescriptorSetLayout setLayout=VK_NULL_HANDLE;VkDescriptorPool descriptorPool=VK_NULL_HANDLE;
 VkPipelineLayout pipelineLayout=VK_NULL_HANDLE;VkPipeline pipeline=VK_NULL_HANDLE;VkCommandPool commandPool=VK_NULL_HANDLE;
 VkSemaphore timeline=VK_NULL_HANDLE;VkFence fence=VK_NULL_HANDLE;uint32_t *spv=NULL;
 VkQueue queue=VK_NULL_HANDLE;uint32_t first=0,second=0;VkResult pendingStatus=VK_SUCCESS;
 const char *layer="VK_LAYER_KHRONOS_validation",*extension=VK_EXT_DEBUG_UTILS_EXTENSION_NAME;
 VkDebugUtilsMessengerCreateInfoEXT dbg={.sType=VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT,.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT,.pfnUserCallback=cb};
 VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.apiVersion=VK_API_VERSION_1_2};
 VkInstanceCreateInfo ic={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pNext=&dbg,.pApplicationInfo=&app,.enabledLayerCount=1,.ppEnabledLayerNames=&layer,.enabledExtensionCount=1,.ppEnabledExtensionNames=&extension};
 uint32_t layerCount=0;CHECK(vkEnumerateInstanceLayerProperties(&layerCount,NULL));
 VkLayerProperties *layers=calloc(layerCount,sizeof(*layers));if(!layers)goto cleanup;
 VkResult lr=vkEnumerateInstanceLayerProperties(&layerCount,layers);uint32_t layerSpec=0,layerImpl=0;
 for(uint32_t i=0;i<layerCount;i++)if(!strcmp(layers[i].layerName,layer)){layerSpec=layers[i].specVersion;layerImpl=layers[i].implementationVersion;}
 free(layers);if(lr!=VK_SUCCESS||!layerSpec)goto cleanup;
 CHECK(vkCreateInstance(&ic,NULL,&instance));
 PFN_vkCreateDebugUtilsMessengerEXT create=(PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT");
 destroy=(PFN_vkDestroyDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT");
 if(!create||!destroy)goto cleanup;
 CHECK(create(instance,&dbg,NULL,&messenger));
 uint32_t n=0;CHECK(vkEnumeratePhysicalDevices(instance,&n,NULL));if(!n)goto cleanup;
 VkPhysicalDevice *physicalDevices=calloc(n,sizeof(*physicalDevices));if(!physicalDevices)goto cleanup;
 VkResult enumerate=vkEnumeratePhysicalDevices(instance,&n,physicalDevices);VkPhysicalDevice physical=physicalDevices[0];free(physicalDevices);if(enumerate!=VK_SUCCESS)goto cleanup;
 VkPhysicalDeviceProperties props;vkGetPhysicalDeviceProperties(physical,&props);
 if(props.deviceType!=VK_PHYSICAL_DEVICE_TYPE_CPU||props.apiVersion<VK_API_VERSION_1_2){fprintf(stderr,"unsupported device scope\n");goto cleanup;}
 VkPhysicalDeviceTimelineSemaphoreFeatures tf={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES};
 VkPhysicalDeviceFeatures2 f2={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2,.pNext=&tf};vkGetPhysicalDeviceFeatures2(physical,&f2);
 if(!tf.timelineSemaphore){fprintf(stderr,"timeline unsupported\n");goto cleanup;}
 fprintf(stderr,"IDENTITY {\"device_type\":%u,\"vendor_id\":%u,\"device_id\":%u,\"driver\":%u,\"api\":%u,\"timeline_supported\":true,\"layer_spec\":%u,\"layer_impl\":%u}\n",props.deviceType,props.vendorID,props.deviceID,props.driverVersion,props.apiVersion,layerSpec,layerImpl);
 vkGetPhysicalDeviceQueueFamilyProperties(physical,&n,NULL);VkQueueFamilyProperties *families=calloc(n,sizeof(*families));if(!families)goto cleanup;
 vkGetPhysicalDeviceQueueFamilyProperties(physical,&n,families);uint32_t family=0;while(family<n&&!(families[family].queueFlags&VK_QUEUE_COMPUTE_BIT))family++;free(families);if(family==n)goto cleanup;
 float priority=1;VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=family,.queueCount=1,.pQueuePriorities=&priority};
 VkDeviceCreateInfo dc={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.pNext=&tf,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};CHECK(vkCreateDevice(physical,&dc,NULL,&device));vkGetDeviceQueue(device,family,0,&queue);
 VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(physical,&mp);
 for(int i=0;i<3;i++){
  VkBufferCreateInfo bc={.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,.size=16,.usage=i==2?VK_BUFFER_USAGE_STORAGE_BUFFER_BIT:VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,.sharingMode=VK_SHARING_MODE_EXCLUSIVE};
  CHECK(vkCreateBuffer(device,&bc,NULL,&buffers[i]));VkMemoryRequirements req;vkGetBufferMemoryRequirements(device,buffers[i],&req);
  uint32_t mt=0;for(;mt<mp.memoryTypeCount;mt++)if((req.memoryTypeBits&(1u<<mt))&&(mp.memoryTypes[mt].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))break;
  if(mt==mp.memoryTypeCount)goto cleanup;
  VkMemoryAllocateInfo ai={.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,.allocationSize=req.size,.memoryTypeIndex=mt};CHECK(vkAllocateMemory(device,&ai,NULL,&memory[i]));CHECK(vkBindBufferMemory(device,buffers[i],memory[i],0));CHECK(vkMapMemory(device,memory[i],0,16,0,&mapped[i]));memset(mapped[i],0,16);
 }
 *(uint32_t*)mapped[0]=42;*(uint32_t*)mapped[1]=99;
 VkDescriptorSetLayoutBinding bindings[2]={{.binding=0,.descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,.descriptorCount=1,.stageFlags=VK_SHADER_STAGE_COMPUTE_BIT},{.binding=1,.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,.descriptorCount=1,.stageFlags=VK_SHADER_STAGE_COMPUTE_BIT}};
 VkDescriptorSetLayoutCreateInfo sl={.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,.bindingCount=2,.pBindings=bindings};CHECK(vkCreateDescriptorSetLayout(device,&sl,NULL,&setLayout));
 VkDescriptorPoolSize sizes[2]={{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,1},{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,1}};
 VkDescriptorPoolCreateInfo dp={.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,.maxSets=1,.poolSizeCount=2,.pPoolSizes=sizes};CHECK(vkCreateDescriptorPool(device,&dp,NULL,&descriptorPool));
 VkDescriptorSetAllocateInfo da={.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,.descriptorPool=descriptorPool,.descriptorSetCount=1,.pSetLayouts=&setLayout};VkDescriptorSet set;CHECK(vkAllocateDescriptorSets(device,&da,&set));
 VkDescriptorBufferInfo infos[2]={{buffers[0],0,16},{buffers[2],0,16}};
 VkWriteDescriptorSet writes[2]={{.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,.dstSet=set,.dstBinding=0,.descriptorCount=1,.descriptorType=VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,.pBufferInfo=&infos[0]},{.sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,.dstSet=set,.dstBinding=1,.descriptorCount=1,.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,.pBufferInfo=&infos[1]}};
 vkUpdateDescriptorSets(device,2,writes,0,NULL);if(errors)goto cleanup;
 FILE *file=fopen(argv[2],"rb");if(!file)goto cleanup;
 if(fseek(file,0,SEEK_END)){fclose(file);goto cleanup;}long bytes=ftell(file);rewind(file);
 if(bytes<=0||bytes%4||bytes>1048576){fclose(file);goto cleanup;}spv=malloc((size_t)bytes);if(!spv){fclose(file);goto cleanup;}size_t read=fread(spv,1,(size_t)bytes,file);fclose(file);if(read!=(size_t)bytes)goto cleanup;
 VkShaderModuleCreateInfo sm={.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,.codeSize=(size_t)bytes,.pCode=spv};CHECK(vkCreateShaderModule(device,&sm,NULL,&shader));
 VkPipelineLayoutCreateInfo pl={.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,.setLayoutCount=1,.pSetLayouts=&setLayout};CHECK(vkCreatePipelineLayout(device,&pl,NULL,&pipelineLayout));
 VkComputePipelineCreateInfo cp={.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,.stage={.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,.stage=VK_SHADER_STAGE_COMPUTE_BIT,.module=shader,.pName="main"},.layout=pipelineLayout};CHECK(vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&cp,NULL,&pipeline));
 VkCommandPoolCreateInfo pc={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,.queueFamilyIndex=family};CHECK(vkCreateCommandPool(device,&pc,NULL,&commandPool));
 VkCommandBufferAllocateInfo ca={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=commandPool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};VkCommandBuffer cmd;CHECK(vkAllocateCommandBuffers(device,&ca,&cmd));
 VkCommandBufferBeginInfo begin={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};CHECK(vkBeginCommandBuffer(cmd,&begin));record(cmd,pipeline,pipelineLayout,set,buffers[2]);CHECK(vkEndCommandBuffer(cmd));
 VkSemaphoreTypeCreateInfo st={.sType=VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO,.semaphoreType=VK_SEMAPHORE_TYPE_TIMELINE,.initialValue=0};
 VkSemaphoreCreateInfo sc={.sType=VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,.pNext=&st};CHECK(vkCreateSemaphore(device,&sc,NULL,&timeline));
 VkFenceCreateInfo fc={.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};CHECK(vkCreateFence(device,&fc,NULL,&fence));
 uint64_t value=1;VkPipelineStageFlags stage=VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT;
 VkTimelineSemaphoreSubmitInfo ts={.sType=VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO,.waitSemaphoreValueCount=1,.pWaitSemaphoreValues=&value};
 VkSubmitInfo submit={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.pNext=&ts,.waitSemaphoreCount=1,.pWaitSemaphores=&timeline,.pWaitDstStageMask=&stage,.commandBufferCount=1,.pCommandBuffers=&cmd};CHECK(vkQueueSubmit(queue,1,&submit,fence));pending=1;
 pendingStatus=vkGetFenceStatus(device,fence);if(pendingStatus!=VK_NOT_READY){fprintf(stderr,"fence unexpectedly ready\n");goto cleanup;}
 phase="pending-update";
 if(bad){vkUpdateDescriptorSets(device,1,writes,0,NULL);if(errors!=1||expected!=1)goto cleanup;}
 if(resetPending){
  phase="pending-reset";
  rejectedCall=vkResetCommandBuffer(cmd,0);
  if(rejectedCall!=VK_ERROR_VALIDATION_FAILED_EXT||errors!=1||expected!=1)goto cleanup;
 }
 phase="release-and-first-readback";
 VkSemaphoreSignalInfo signal={.sType=VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO,.semaphore=timeline,.value=1};CHECK(vkSignalSemaphore(device,&signal));
 CHECK(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL));pending=0;first=*(uint32_t*)mapped[2];if(first!=42)goto cleanup;
 /* Completion permits ordinary update; re-record since the update invalidates the old executable command buffer. */
 phase="completed-update-rerecord";
 infos[0].buffer=buffers[1];vkUpdateDescriptorSets(device,1,writes,0,NULL);
 CHECK(vkResetFences(device,1,&fence));
 if(stale){
  phase="stale-submit";
  submit.pNext=NULL;submit.waitSemaphoreCount=0;submit.pWaitSemaphores=NULL;submit.pWaitDstStageMask=NULL;
  rejectedCall=vkQueueSubmit(queue,1,&submit,fence);
  if(rejectedCall!=VK_ERROR_VALIDATION_FAILED_EXT||errors!=1||expected!=1)goto cleanup;
  if(vkGetFenceStatus(device,fence)!=VK_NOT_READY)goto cleanup;
 }
 phase="recovery-reset-rerecord";
 CHECK(vkResetCommandBuffer(cmd,0));CHECK(vkBeginCommandBuffer(cmd,&begin));record(cmd,pipeline,pipelineLayout,set,buffers[2]);CHECK(vkEndCommandBuffer(cmd));
 submit.pNext=NULL;submit.waitSemaphoreCount=0;submit.pWaitSemaphores=NULL;submit.pWaitDstStageMask=NULL;
 CHECK(vkQueueSubmit(queue,1,&submit,fence));pending=1;CHECK(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL));pending=0;second=*(uint32_t*)mapped[2];
 rc=(second==(wrong?100u:99u)&&errors==expectedErrors&&expected==expectedErrors)?0:6;
cleanup:
 phase="cleanup";
 if(device){
  if(pending&&timeline){VkSemaphoreSignalInfo release={.sType=VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO,.semaphore=timeline,.value=1};uint64_t v=0;if(vkGetSemaphoreCounterValue(device,timeline,&v)==VK_SUCCESS&&v<1)(void)vkSignalSemaphore(device,&release);}
  if(vkDeviceWaitIdle(device)!=VK_SUCCESS)rc=2;
  if(fence)vkDestroyFence(device,fence,NULL);
  if(timeline)vkDestroySemaphore(device,timeline,NULL);
  if(commandPool)vkDestroyCommandPool(device,commandPool,NULL);
  if(pipeline)vkDestroyPipeline(device,pipeline,NULL);
  if(pipelineLayout)vkDestroyPipelineLayout(device,pipelineLayout,NULL);
  if(shader)vkDestroyShaderModule(device,shader,NULL);
  if(descriptorPool)vkDestroyDescriptorPool(device,descriptorPool,NULL);
  if(setLayout)vkDestroyDescriptorSetLayout(device,setLayout,NULL);
  for(int i=0;i<3;i++){if(mapped[i])vkUnmapMemory(device,memory[i]);if(buffers[i])vkDestroyBuffer(device,buffers[i],NULL);if(memory[i])vkFreeMemory(device,memory[i],NULL);}
  vkDestroyDevice(device,NULL);
 }
 if(messenger&&destroy)destroy(instance,messenger,NULL);
 if(instance)vkDestroyInstance(instance,NULL);
 free(spv);
 if(rc==0&&(errors!=expectedErrors||expected!=expectedErrors))rc=9;
 printf("{\"mode\":\"%s\",\"fence_not_ready\":%s,\"first\":%u,\"second\":%u,\"errors\":%u,\"expected_vuid_count\":%u,\"rejected_call_result\":%d,\"exit_code\":%d}\n",argv[1],pendingStatus==VK_NOT_READY?"true":"false",first,second,errors,expected,rejectedCall,rc);
 return rc;
}
