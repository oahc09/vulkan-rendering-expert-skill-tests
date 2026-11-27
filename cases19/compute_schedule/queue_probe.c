/* HOST capability/creation observation only: no command buffers or submissions. */
#include <vulkan/vulkan.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static void json_string(const char *s) {
    putchar('"');
    for (const unsigned char *p=(const unsigned char *)s; *p; ++p) {
        if (*p=='"' || *p=='\\') { putchar('\\'); putchar(*p); }
        else if (*p<32 || *p>=127) printf("\\u%04x", *p);
        else putchar(*p);
    }
    putchar('"');
}
int main(void) {
    VkInstance instance=VK_NULL_HANDLE; VkDevice device=VK_NULL_HANDLE;
    VkPhysicalDevice *physical=NULL; VkQueueFamilyProperties *families=NULL;
    int exit_code=1; uint32_t n=0, nf=0;
    VkApplicationInfo app={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName="bounded-queue-creation-probe",.apiVersion=VK_API_VERSION_1_0};
    VkInstanceCreateInfo ici={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pApplicationInfo=&app};
    VkResult r=vkCreateInstance(&ici,NULL,&instance);
    if(r!=VK_SUCCESS){fprintf(stderr,"vkCreateInstance=%d\n",r);goto cleanup;}
    r=vkEnumeratePhysicalDevices(instance,&n,NULL);
    if(r!=VK_SUCCESS || !n){fprintf(stderr,"enumerate count result=%d count=%u\n",r,n);goto cleanup;}
    physical=calloc(n,sizeof(*physical));if(!physical)goto cleanup;
    r=vkEnumeratePhysicalDevices(instance,&n,physical);
    if(r!=VK_SUCCESS || !n){fprintf(stderr,"enumerate values result=%d count=%u\n",r,n);goto cleanup;}
    /* Deliberately report selection of device zero, not a best-device policy. */
    VkPhysicalDevice pd=physical[0]; VkPhysicalDeviceProperties props;
    vkGetPhysicalDeviceProperties(pd,&props);
    vkGetPhysicalDeviceQueueFamilyProperties(pd,&nf,NULL);
    if(!nf){fprintf(stderr,"no queue families\n");goto cleanup;}
    families=calloc(nf,sizeof(*families));if(!families)goto cleanup;
    uint32_t capacity=nf;vkGetPhysicalDeviceQueueFamilyProperties(pd,&nf,families);
    if(!nf || nf>capacity){fprintf(stderr,"invalid family count\n");goto cleanup;}
    uint32_t graphics=UINT32_MAX,compute=UINT32_MAX;
    for(uint32_t i=0;i<nf;i++)if(families[i].queueCount && (families[i].queueFlags&VK_QUEUE_GRAPHICS_BIT)){graphics=i;break;}
    for(uint32_t i=0;i<nf;i++)if(families[i].queueCount && (families[i].queueFlags&VK_QUEUE_COMPUTE_BIT) && !(families[i].queueFlags&VK_QUEUE_GRAPHICS_BIT)){compute=i;break;}
    if(compute==UINT32_MAX && graphics!=UINT32_MAX && (families[graphics].queueFlags&VK_QUEUE_COMPUTE_BIT))compute=graphics;
    if(compute==UINT32_MAX)for(uint32_t i=0;i<nf;i++)if(families[i].queueCount && (families[i].queueFlags&VK_QUEUE_COMPUTE_BIT)){compute=i;break;}
    if(graphics==UINT32_MAX || compute==UINT32_MAX){fprintf(stderr,"required graphics/compute family unavailable\n");exit_code=3;goto cleanup;}
    float priorities[2]={1.0f,1.0f};
    uint32_t compute_index=(graphics==compute && families[graphics].queueCount>=2)?1:0;
    VkDeviceQueueCreateInfo qci[2]={{.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=graphics,.queueCount=(graphics==compute?compute_index+1:1),.pQueuePriorities=priorities},
        {.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=compute,.queueCount=1,.pQueuePriorities=priorities}};
    VkDeviceCreateInfo dci={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=(graphics==compute?1:2),.pQueueCreateInfos=qci};
    r=vkCreateDevice(pd,&dci,NULL,&device);
    if(r!=VK_SUCCESS){fprintf(stderr,"vkCreateDevice=%d\n",r);goto cleanup;}
    VkQueue gq=VK_NULL_HANDLE,cq=VK_NULL_HANDLE;
    vkGetDeviceQueue(device,graphics,0,&gq);vkGetDeviceQueue(device,compute,compute_index,&cq);
    if(gq==VK_NULL_HANDLE || cq==VK_NULL_HANDLE){fprintf(stderr,"null requested queue handle\n");goto cleanup;}
    printf("{\"schema\":1,\"status\":\"QUEUE_CREATION_OBSERVED\",\"device_index\":0,\"physical_device_count\":%u,\"device\":{\"name\":",n);
    json_string(props.deviceName);
    printf(",\"vendorID\":%u,\"deviceID\":%u,\"deviceType\":%u,\"apiVersion\":%u,\"driverVersion\":%u},\"families\":[",props.vendorID,props.deviceID,props.deviceType,props.apiVersion,props.driverVersion);
    for(uint32_t i=0;i<nf;i++)printf("%s{\"family\":%u,\"flags\":%u,\"count\":%u}",i?",":"",i,families[i].queueFlags,families[i].queueCount);
    printf("],\"created\":[");int comma=0;
    for(uint32_t i=0;i<dci.queueCreateInfoCount;i++)for(uint32_t j=0;j<qci[i].queueCount;j++)printf("%s{\"family\":%u,\"index\":%u}",comma++?",":"",qci[i].queueFamilyIndex,j);
    printf("],\"graphics\":{\"family\":%u,\"index\":0},\"compute\":{\"family\":%u,\"index\":%u},\"get_queue_nonnull\":true,\"same_queue_handle\":%s,\"instance_api_requested\":%u,\"enabled_features\":[],\"enabled_extensions\":[],\"gpu_work_submitted\":false}\n",graphics,compute,compute_index,gq==cq?"true":"false",VK_API_VERSION_1_0);
    exit_code=0;
cleanup:
    if(device)vkDestroyDevice(device,NULL);
    if(instance)vkDestroyInstance(instance,NULL);
    free(families);free(physical);return exit_code;
}
