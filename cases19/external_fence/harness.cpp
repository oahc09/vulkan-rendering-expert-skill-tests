// Original HOST harness; upstream FencePool .cpp/.h are extracted unchanged.
#include "fence_pool.h"
#include "core/device.h"
#include <iostream>
#include <string>
uint64_t last_timeout=0; unsigned calls=0; VkResult response=VK_SUCCESS;
VKAPI_ATTR VkResult VKAPI_CALL vkCreateFence(VkDevice,const VkFenceCreateInfo*,const VkAllocationCallbacks*,VkFence*f){*f=reinterpret_cast<VkFence>(uintptr_t(7));return VK_SUCCESS;}
VKAPI_ATTR void VKAPI_CALL vkDestroyFence(VkDevice,VkFence,const VkAllocationCallbacks*){}
VKAPI_ATTR VkResult VKAPI_CALL vkResetFences(VkDevice,uint32_t,const VkFence*){return VK_SUCCESS;}
VKAPI_ATTR VkResult VKAPI_CALL vkWaitForFences(VkDevice d,uint32_t n,const VkFence*f,VkBool32 all,uint64_t timeout){if(d!=reinterpret_cast<VkDevice>(uintptr_t(41))||n!=1||*f!=reinterpret_cast<VkFence>(uintptr_t(7))||all!=VK_TRUE) throw std::runtime_error("API argument error");last_timeout=timeout;++calls;return response;}
int main(int argc,char**argv){
 if(argc!=2||(std::string(argv[1])!="fixed"&&std::string(argv[1])!="old")){std::cerr<<"INVALID_MODE\n";return 2;}
 try {bool fixed=std::string(argv[1])=="fixed";vkb::Device device;vkb::FencePool p(device);
 if(p.wait()!=VK_SUCCESS||calls)return 3;
 std::cout<<"empty wait=0 calls=0\n";p.request_fence();
 auto check=[&](const char*label,uint64_t want,VkResult got,VkResult expected){std::cout<<label<<" timeout="<<last_timeout<<" result="<<got<<" calls="<<calls<<"\n";if(last_timeout!=want||got!=expected)throw std::runtime_error("ORACLE_MISMATCH");};
 check("default",fixed?UINT64_MAX:UINT32_MAX,p.wait(),VK_SUCCESS);
 for(uint64_t t:std::vector<uint64_t>{0,UINT32_MAX,uint64_t(UINT32_MAX)+1,UINT64_MAX}){VkResult r=p.wait(t);check("explicit",fixed?t:uint32_t(t),r,VK_SUCCESS);}
 for(VkResult r:std::vector<VkResult>{VK_TIMEOUT,VK_ERROR_DEVICE_LOST}){response=r;check("result-propagation",fixed?UINT64_MAX:UINT32_MAX,p.wait(),r);}
 response=VK_SUCCESS;if(p.reset()!=VK_SUCCESS)return 4;unsigned prior=calls;if(p.wait()!=VK_SUCCESS||calls!=prior)return 5;
 std::cout<<"reset-empty no-extra-wait\n";
 } catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 6;}
 return 0;
}
