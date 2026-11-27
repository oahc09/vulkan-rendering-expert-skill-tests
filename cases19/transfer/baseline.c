/* Authored real Vulkan transfer regression, deliberately faulty baseline.
 * Not an external engine bug or hardware acceptance. */
#include <vulkan/vulkan.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int count;
static VKAPI_ATTR VkBool32 VKAPI_CALL callback(VkDebugUtilsMessageSeverityFlagBitsEXT sev,VkDebugUtilsMessageTypeFlagsEXT type,const VkDebugUtilsMessengerCallbackDataEXT *d,void *user) {
 (void)type;(void)user;
 if(!(sev&VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT))return VK_FALSE;
 if(count++)printf(",");
 printf("{\"pMessageIdName\":\"%s\",\"pMessage\":\"omitted by probe\",\"objectCount\":%u,\"pObjects\":[",d->pMessageIdName?d->pMessageIdName:"",d->objectCount);
 for(uint32_t i=0;i<d->objectCount;i++){if(i)printf(",");printf("{\"objectType\":%d,\"objectHandle\":%llu}",d->pObjects[i].objectType,(unsigned long long)d->pObjects[i].objectHandle);}
 printf("]}");
 return VK_TRUE; /* Abort invalid call after observation; never send invalid command to ICD. */
}
#define OK(x) do { VkResult r=(x);if(r!=VK_SUCCESS){fprintf(stderr,"failure %s: %d\n",#x,r);return 2;} } while(0)
int main(int argc,char**argv){
 if(argc!=2||(strcmp(argv[1],"bad")&&strcmp(argv[1],"good")))return 7;
 int bad=!strcmp(argv[1],"bad");
#ifndef TRANSFER_FIX
#define TRANSFER_FIX 0
#endif
 const char *layer="VK_LAYER_KHRONOS_validation";
 const char *exts[]={VK_EXT_DEBUG_UTILS_EXTENSION_NAME,VK_EXT_VALIDATION_FEATURES_EXTENSION_NAME};
 VkDebugUtilsMessengerCreateInfoEXT debug={.sType=VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT,.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT,.pfnUserCallback=callback};
 VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.apiVersion=VK_API_VERSION_1_1};
 uint32_t lc=0;OK(vkEnumerateInstanceLayerProperties(&lc,0));
 VkLayerProperties *layers=calloc(lc,sizeof(*layers));OK(vkEnumerateInstanceLayerProperties(&lc,layers));
 uint32_t spec=0,impl=0;for(uint32_t i=0;i<lc;i++)if(!strcmp(layers[i].layerName,layer)){spec=layers[i].specVersion;impl=layers[i].implementationVersion;}free(layers);
 VkValidationFeatureEnableEXT enable=VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT;
 VkValidationFeaturesEXT vf={.sType=VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT,.pNext=&debug,.enabledValidationFeatureCount=1,.pEnabledValidationFeatures=&enable};
 VkInstanceCreateInfo ci={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pNext=&vf,.pApplicationInfo=&app,.enabledLayerCount=1,.ppEnabledLayerNames=&layer,.enabledExtensionCount=2,.ppEnabledExtensionNames=exts};
 printf("["); VkInstance instance;OK(vkCreateInstance(&ci,0,&instance));
 PFN_vkCreateDebugUtilsMessengerEXT create=(PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT");
 PFN_vkDestroyDebugUtilsMessengerEXT destroy=(PFN_vkDestroyDebugUtilsMessengerEXT)vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT");
 VkDebugUtilsMessengerEXT messenger;OK(create(instance,&debug,0,&messenger));
 uint32_t n=0;OK(vkEnumeratePhysicalDevices(instance,&n,0));if(!n)return 3;
 VkPhysicalDevice *devices=calloc(n,sizeof(*devices));OK(vkEnumeratePhysicalDevices(instance,&n,devices));
 VkPhysicalDevice physical=devices[0];free(devices);
 VkPhysicalDeviceProperties props;vkGetPhysicalDeviceProperties(physical,&props);
 fprintf(stderr,"IDENTITY {\"device_type\":%u,\"device_id\":%u,\"vendor_id\":%u,\"driver\":%u,\"api\":%u,\"layer_spec\":%u,\"layer_impl\":%u}\n",props.deviceType,props.deviceID,props.vendorID,props.driverVersion,props.apiVersion,spec,impl);
 vkGetPhysicalDeviceQueueFamilyProperties(physical,&n,0);VkQueueFamilyProperties *q=calloc(n,sizeof(*q));vkGetPhysicalDeviceQueueFamilyProperties(physical,&n,q);
 uint32_t family=0;while(family<n&&(!q[family].queueCount||!(q[family].queueFlags&VK_QUEUE_TRANSFER_BIT)))family++;free(q);if(family==n)return 4;
 float priority=1;VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=family,.queueCount=1,.pQueuePriorities=&priority};
 VkDeviceCreateInfo dc={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};VkDevice device;OK(vkCreateDevice(physical,&dc,0,&device));

 VkBuffer buffers[2];VkDeviceMemory mem[2];void *mapped[2];
 VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(physical,&mp);
 for(int i=0;i<2;i++){
  VkBufferCreateInfo bc={.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,.size=256,.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT,.sharingMode=VK_SHARING_MODE_EXCLUSIVE};
  OK(vkCreateBuffer(device,&bc,0,&buffers[i]));VkMemoryRequirements req;vkGetBufferMemoryRequirements(device,buffers[i],&req);
  uint32_t mt=0;for(;mt<mp.memoryTypeCount;mt++)if((req.memoryTypeBits&(1u<<mt))&&(mp.memoryTypes[mt].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))break;
  if(mt==mp.memoryTypeCount)return 8;
  VkMemoryAllocateInfo ai={.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,.allocationSize=req.size,.memoryTypeIndex=mt};OK(vkAllocateMemory(device,&ai,0,&mem[i]));OK(vkBindBufferMemory(device,buffers[i],mem[i],0));OK(vkMapMemory(device,mem[i],0,256,0,&mapped[i]));memset(mapped[i],0,256);
 }
 VkCommandPoolCreateInfo pc={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.queueFamilyIndex=family};VkCommandPool pool;OK(vkCreateCommandPool(device,&pc,0,&pool));
 VkCommandBufferAllocateInfo ca={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=pool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};VkCommandBuffer cmd;OK(vkAllocateCommandBuffers(device,&ca,&cmd));
 VkCommandBufferBeginInfo begin={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};OK(vkBeginCommandBuffer(cmd,&begin));
 vkCmdFillBuffer(cmd,buffers[0],0,256,0x12345678);
 if(!bad||TRANSFER_FIX){
  VkBufferMemoryBarrier b={.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT,.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.buffer=buffers[0],.offset=0,.size=256};
  vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,0,1,&b,0,0);
 }
 VkBufferCopy copy={.size=256};vkCmdCopyBuffer(cmd,buffers[0],buffers[1],1,&copy);
 VkBufferMemoryBarrier host={.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,.dstAccessMask=VK_ACCESS_HOST_READ_BIT,.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.buffer=buffers[1],.offset=0,.size=256};
 vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,0,0,1,&host,0,0);
 OK(vkEndCommandBuffer(cmd));VkQueue queue;vkGetDeviceQueue(device,family,0,&queue);
 VkFenceCreateInfo fc={.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VkFence fence;OK(vkCreateFence(device,&fc,0,&fence));
 VkSubmitInfo submit={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.commandBufferCount=1,.pCommandBuffers=&cmd};OK(vkQueueSubmit(queue,1,&submit,fence));OK(vkWaitForFences(device,1,&fence,VK_TRUE,10000000000ULL));
 int matches=0;for(int i=0;i<64;i++)matches+=((uint32_t*)mapped[1])[i]==0x12345678;
 fprintf(stderr,"RESULT matching_words=%d errors=%d patched=%d\n",matches,count,TRANSFER_FIX);
 vkDestroyFence(device,fence,0);vkDestroyCommandPool(device,pool,0);
 for(int i=0;i<2;i++){vkUnmapMemory(device,mem[i]);vkDestroyBuffer(device,buffers[i],0);vkFreeMemory(device,mem[i],0);}
 vkDestroyDevice(device,0);destroy(instance,messenger,0);vkDestroyInstance(instance,0);printf("]\n");
 return (bad&&!TRANSFER_FIX)?(count>0?0:5):(count==0&&matches==64?0:6);
}
