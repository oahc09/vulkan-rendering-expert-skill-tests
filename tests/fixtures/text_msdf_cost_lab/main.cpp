// SPDX-License-Identifier: MIT
#include "cost_reused.hpp"
#include <memory>
int main(int argc,char**argv){try{
 if(argc!=9)throw std::runtime_error("usage baselineShaders binaryShaders linearShaders atlas newSamples baselineReference binaryReference linearReference");
 std::filesystem::path path=argv[5];if(std::filesystem::exists(path))throw std::runtime_error("existing samples");
 std::ifstream in(argv[4],std::ios::binary|std::ios::ate);if(!in||in.tellg()!=65*49*16)throw std::runtime_error("atlas size");
 std::vector<float> atlas(65*49*4);in.seekg(0);in.read((char*)atlas.data(),atlas.size()*4);for(float v:atlas)if(!std::isfinite(v)||v<0||v>1)throw std::runtime_error("atlas range");
 std::array<std::vector<float>,3> expected;
 for(int i=0;i<3;i++){std::ifstream ref(argv[6+i],std::ios::binary|std::ios::ate);if(!ref||ref.tellg()!=65*49*16)throw std::runtime_error("reference size");expected[i].resize(65*49*4);ref.seekg(0);ref.read((char*)expected[i].data(),65*49*16);for(float v:expected[i])if(!std::isfinite(v))throw std::runtime_error("nonfinite reference");}
 std::array<std::unique_ptr<TextLab>,3> labs;for(int i=0;i<3;i++)labs[i]=std::make_unique<TextLab>(argv[i+1]);
 std::ofstream out(path);const char*names[]={"baseline","binary16","linear4"};
 for(int i=0;i<3;i++){
  auto&l=*labs[i];uint32_t count=0;vkGetPhysicalDeviceQueueFamilyProperties(l.physical,&count,nullptr);std::vector<VkQueueFamilyProperties> qp(count);vkGetPhysicalDeviceQueueFamilyProperties(l.physical,&count,qp.data());
  l.costBits=qp.at(l.family).timestampValidBits;l.costPeriod=l.properties.limits.timestampPeriod;
  out<<"{\"capability\":\""<<names[i]<<"\",\"timestampValidBits\":"<<l.costBits<<",\"timestampPeriod\":"<<l.costPeriod<<",\"timestampComputeAndGraphics\":"<<l.properties.limits.timestampComputeAndGraphics<<",\"validation\":"<<l.validation<<",\"deviceType\":"<<l.properties.deviceType<<",\"vendorID\":"<<l.properties.vendorID<<",\"driverVersion\":"<<l.properties.driverVersion<<",\"deviceName\":"<<std::quoted(l.properties.deviceName)<<"}\n";
  if(l.properties.deviceType!=VK_PHYSICAL_DEVICE_TYPE_CPU){out<<"{\"status\":\"NOT_MEASURED\",\"reason\":\"software CPU device required\"}\n";return 0;}
  if(!l.costBits||l.costBits>64||!std::isfinite(l.costPeriod)||l.costPeriod<=0||!l.properties.limits.timestampComputeAndGraphics){out<<"{\"status\":\"NOT_MEASURED\",\"reason\":\"timestamp capability unavailable\"}\n";return 0;}
  VkQueryPoolCreateInfo q{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};q.queryType=VK_QUERY_TYPE_TIMESTAMP;q.queryCount=2;
  VkResult result=vkCreateQueryPool(l.device,&q,nullptr,&l.costQueries);if(result!=VK_SUCCESS){out<<"{\"status\":\"NOT_MEASURED\",\"reason\":\"query pool creation failed\",\"result\":"<<result<<"}\n";return 0;}
 }
 // Five complete warmup cycles, then thirty measured cycles. Rotate first mode.
 for(int cycle=0;cycle<35;cycle++)for(int offset=0;offset<3;offset++){
  int i=(cycle+offset)%3;auto&l=*labs[i];auto pixels=l.draw(atlas,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
  for(int j=0;j<3;j++)for(float v:pixels[j])if(!std::isfinite(v))throw std::runtime_error("nonfinite readback");
  for(size_t j=0;j<pixels[0].size();j++)if(std::abs(pixels[0][j]-expected[i][j])>0.000002f)throw std::runtime_error("timed render differs from validated preparation");
  float sent[2][4]={{.125f,-.25f,.5f,1},{37,91,12,1}};for(int k=1;k<3;k++)for(size_t j=0;j<pixels[k].size();j++)if(pixels[k][j]!=sent[k-1][j%4])throw std::runtime_error("UNUSED sentinel changed");
  if(cycle>=5)out<<std::setprecision(17)<<"{\"mode\":\""<<names[i]<<"\",\"cycle\":"<<cycle-5<<",\"gpu_renderpass_ns\":"<<l.costGpuNs<<",\"cpu_submit_ns\":"<<l.costSubmitNs<<",\"cpu_wait_ns\":"<<l.costWaitNs<<"}\n";
 }
 for(auto&l:labs){vkDestroyQueryPool(l->device,l->costQueries,nullptr);l->costQueries=VK_NULL_HANDLE;}
 if(validationErrors)throw std::runtime_error("validation diagnostics");out<<"{\"status\":\"MEASURED_SOFTWARE_ONLY\"}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
