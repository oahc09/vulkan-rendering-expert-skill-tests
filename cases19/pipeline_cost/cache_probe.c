/* Actual cache round trip and CPU call intervals; no submitted workload or speedup claim. */
#define _POSIX_C_SOURCE 200809L
#include <vulkan/vulkan.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#define CHECK(x) do{VkResult r=(x);if(r!=VK_SUCCESS){fprintf(stderr,"%s=%d\n",#x,r);goto done;}}while(0)
static uint64_t now(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;}
int main(int argc,char**argv){
 if(argc!=3)return 64;
 int rc=2;VkInstance in=0;VkDevice d=0;VkShaderModule s=0;VkPipelineLayout l=0;VkPipelineCache caches[2]={0};VkPipeline pipes[2]={0};uint32_t *code=0;void*blob=0;void*diskblob=0;VkPhysicalDevice *devices=0;VkQueueFamilyProperties*qs=0;
 FILE*f=fopen(argv[1],"rb");if(!f)return 2;if(fseek(f,0,SEEK_END)){fclose(f);return 2;}long size=ftell(f);rewind(f);if(size<=0||size%4||size>1048576){fclose(f);return 2;}code=malloc((size_t)size);if(!code){fclose(f);return 2;}size_t rd=fread(code,1,(size_t)size,f);fclose(f);if(rd!=(size_t)size)goto done;
 VkApplicationInfo a={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.apiVersion=VK_API_VERSION_1_0};VkInstanceCreateInfo i={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pApplicationInfo=&a};CHECK(vkCreateInstance(&i,0,&in));
 uint32_t n=0;CHECK(vkEnumeratePhysicalDevices(in,&n,0));if(!n)goto done;devices=calloc(n,sizeof(*devices));if(!devices)goto done;CHECK(vkEnumeratePhysicalDevices(in,&n,devices));if(!n)goto done;VkPhysicalDevice p=devices[0];VkPhysicalDeviceProperties props;vkGetPhysicalDeviceProperties(p,&props);
 vkGetPhysicalDeviceQueueFamilyProperties(p,&n,0);if(!n)goto done;qs=calloc(n,sizeof(*qs));if(!qs)goto done;vkGetPhysicalDeviceQueueFamilyProperties(p,&n,qs);uint32_t q=0;while(q<n&&!(qs[q].queueCount&&(qs[q].queueFlags&VK_QUEUE_COMPUTE_BIT)))q++;if(q==n)goto done;
 float pri=1;VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=q,.queueCount=1,.pQueuePriorities=&pri};VkDeviceCreateInfo di={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};CHECK(vkCreateDevice(p,&di,0,&d));
 VkShaderModuleCreateInfo si={.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,.codeSize=(size_t)size,.pCode=code};CHECK(vkCreateShaderModule(d,&si,0,&s));VkPipelineLayoutCreateInfo li={.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};CHECK(vkCreatePipelineLayout(d,&li,0,&l));
 VkPipelineCacheCreateInfo ci={.sType=VK_STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO};CHECK(vkCreatePipelineCache(d,&ci,0,&caches[0]));VkComputePipelineCreateInfo cp={.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,.stage={.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,.stage=VK_SHADER_STAGE_COMPUTE_BIT,.module=s,.pName="main"},.layout=l};
 uint64_t t0=now();CHECK(vkCreateComputePipelines(d,caches[0],1,&cp,0,&pipes[0]));uint64_t t1=now();if(!t0||t1<t0)goto done;
 size_t bs=0;CHECK(vkGetPipelineCacheData(d,caches[0],&bs,0));if(!bs||bs>67108864)goto done;blob=malloc(bs);if(!blob)goto done;CHECK(vkGetPipelineCacheData(d,caches[0],&bs,blob));
 /* Persist and re-read unmodified bytes; only this exact-device export is imported. */
 f=fopen(argv[2],"wbx");if(!f)goto done;size_t wr=fwrite(blob,1,bs,f);int closed=fclose(f);if(wr!=bs||closed)goto done;
 diskblob=malloc(bs);if(!diskblob)goto done;f=fopen(argv[2],"rb");if(!f)goto done;rd=fread(diskblob,1,bs,f);int extra=fgetc(f);closed=fclose(f);if(rd!=bs||extra!=EOF||closed||memcmp(blob,diskblob,bs))goto done;
 ci.initialDataSize=bs;ci.pInitialData=diskblob;CHECK(vkCreatePipelineCache(d,&ci,0,&caches[1]));uint64_t t2=now();CHECK(vkCreateComputePipelines(d,caches[1],1,&cp,0,&pipes[1]));uint64_t t3=now();if(!t2||t3<t2)goto done;

 printf("{\"schema\":1,\"status\":\"CACHE_ROUNDTRIP_CREATED\",\"vendor_id\":%u,\"device_id\":%u,\"driver\":%u,\"api\":%u,\"device_type\":%u,\"pipeline_cache_uuid\":\"",props.vendorID,props.deviceID,props.driverVersion,props.apiVersion,props.deviceType);for(uint32_t k=0;k<VK_UUID_SIZE;k++)printf("%02x",props.pipelineCacheUUID[k]);printf("\",\"cache_bytes\":%zu,\"empty_cache_create_cpu_ns\":%llu,\"restored_cache_create_cpu_ns\":%llu,\"gpu_work_submitted\":false,\"performance_comparison_valid\":false,\"cache_hit_observed\":false}\n",bs,(unsigned long long)(t1-t0),(unsigned long long)(t3-t2));rc=0;
 done:if(d){for(int k=0;k<2;k++){if(pipes[k])vkDestroyPipeline(d,pipes[k],0);if(caches[k])vkDestroyPipelineCache(d,caches[k],0);}if(l)vkDestroyPipelineLayout(d,l,0);if(s)vkDestroyShaderModule(d,s,0);vkDestroyDevice(d,0);}if(in)vkDestroyInstance(in,0);free(qs);free(devices);free(blob);free(diskblob);free(code);return rc;
}
