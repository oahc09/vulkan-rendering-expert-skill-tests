/* Real Validation callback probe; software ICD only, not GPU acceptance. */
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
 return VK_TRUE; /* Abort invalid call after observation; never send invalid size to ICD. */
}
#define OK(x) do { VkResult r=(x);if(r!=VK_SUCCESS){fprintf(stderr,"failure %s: %d\n",#x,r);return 2;} } while(0)
int main(int argc,char**argv){
 if(argc!=2||(strcmp(argv[1],"bad")&&strcmp(argv[1],"good")))return 7;
 int bad=!strcmp(argv[1],"bad");
 const char *layer="VK_LAYER_KHRONOS_validation",*ext=VK_EXT_DEBUG_UTILS_EXTENSION_NAME;
 VkDebugUtilsMessengerCreateInfoEXT debug={.sType=VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT,.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT,.pfnUserCallback=callback};
 VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.apiVersion=VK_API_VERSION_1_1};
 uint32_t lc=0;OK(vkEnumerateInstanceLayerProperties(&lc,0));
 VkLayerProperties *layers=calloc(lc,sizeof(*layers));OK(vkEnumerateInstanceLayerProperties(&lc,layers));
 uint32_t spec=0,impl=0;for(uint32_t i=0;i<lc;i++)if(!strcmp(layers[i].layerName,layer)){spec=layers[i].specVersion;impl=layers[i].implementationVersion;}free(layers);
 VkInstanceCreateInfo ci={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pNext=&debug,.pApplicationInfo=&app,.enabledLayerCount=1,.ppEnabledLayerNames=&layer,.enabledExtensionCount=1,.ppEnabledExtensionNames=&ext};
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
 uint32_t family=0;while(family<n&&!q[family].queueCount)family++;free(q);if(family==n)return 4;
 float priority=1;VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=family,.queueCount=1,.pQueuePriorities=&priority};
 VkDeviceCreateInfo dc={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};VkDevice device;OK(vkCreateDevice(physical,&dc,0,&device));
 VkBufferCreateInfo bc={.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,.size=bad?0:16,.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT,.sharingMode=VK_SHARING_MODE_EXCLUSIVE};
 VkBuffer buffer=VK_NULL_HANDLE;VkResult result=vkCreateBuffer(device,&bc,0,&buffer);
 if(result==VK_SUCCESS)vkDestroyBuffer(device,buffer,0);
 vkDestroyDevice(device,0);destroy(instance,messenger,0);vkDestroyInstance(instance,0);printf("]\n");
 return bad?(result!=VK_SUCCESS&&count>0?0:5):(result==VK_SUCCESS&&count==0?0:6);
}
