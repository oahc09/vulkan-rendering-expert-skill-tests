// SPDX-License-Identifier: MIT
// Reuse the existing fixture's allocation, shaders, draw, barriers and lifetime.
#define main engine_scale_lab_original_main
#include "../engine_scale_lab/main.cpp"
#undef main
static void unitValue(float value){
 if(!std::isfinite(value)||value<0.f||value>1.00001f)throw std::runtime_error("Nonfinite/out-of-range unit signal");
}
static void pgm(const std::filesystem::path &path,const float* data,uint32_t w,uint32_t h,uint32_t stride=1,uint32_t offset=0){
 std::ofstream f(path,std::ios::binary);f<<"P5\n"<<w<<" "<<h<<"\n255\n";
 for(uint32_t i=0;i<w*h;i++){unitValue(data[i*stride+offset]);uint8_t b=uint8_t(std::clamp(data[i*stride+offset],0.f,1.f)*255.f+.5f);f.write((char*)&b,1);}
}
#include "query_runtime.hpp"
int main(int argc,char**argv){try{
 if(argc!=3&&argc!=4)throw std::runtime_error("usage: hybrid_quality_lab SHADER_DIR NEW_OUTPUT_DIR [--disable-query]");
 bool disableQuery=argc==4;if(disableQuery&&std::string(argv[3])!="--disable-query")throw std::runtime_error("Unknown option");
 std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("Refuse existing output directory");
 Vulkan v(65*49,argv[1],true);uint32_t pixels=v.width*v.height;
 uint32_t ec=0;VK(vkEnumerateDeviceExtensionProperties(v.physical,nullptr,&ec,nullptr));std::vector<VkExtensionProperties> ex(ec);VK(vkEnumerateDeviceExtensionProperties(v.physical,nullptr,&ec,ex.data()));
 auto has=[&](const char*name){return std::any_of(ex.begin(),ex.end(),[&](auto&e){return std::string(e.extensionName)==name;});};
 bool queryExt=has(VK_KHR_RAY_QUERY_EXTENSION_NAME),asExt=has(VK_KHR_ACCELERATION_STRUCTURE_EXTENSION_NAME);
 VkPhysicalDeviceRayQueryFeaturesKHR rq{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_QUERY_FEATURES_KHR};VkPhysicalDeviceAccelerationStructureFeaturesKHR as{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_FEATURES_KHR};VkPhysicalDeviceVulkan12Features f12{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};VkPhysicalDeviceFeatures2 f2{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};f2.pNext=&f12;if(asExt){f12.pNext=&as;if(queryExt)as.pNext=&rq;}vkGetPhysicalDeviceFeatures2(v.physical,&f2);
 std::cout<<"{\"ray_query_extension\":"<<queryExt<<",\"ray_query_feature\":"<<rq.rayQuery<<",\"acceleration_structure\":"<<as.accelerationStructure<<",\"buffer_device_address\":"<<f12.bufferDeviceAddress<<",\"ray_query_execution\":\""<<((rq.rayQuery&&as.accelerationStructure&&f12.bufferDeviceAddress)?"SUPPORTED_PENDING_RUN":"UNSUPPORTED_DEVICE")<<"\",\"omm_execution\":\"UNIMPLEMENTED\",\"omm_ext_advertised\":"<<has("VK_EXT_opacity_micromap")<<",\"omm_khr_advertised\":"<<has("VK_KHR_opacity_micromap")<<"}\n";
 auto lighting=v.compute("lighting.comp"),temporal=v.compute("temporal.comp"),spatial=v.compute("spatial.comp");
 std::memset(v.buffers[2].map,0,size_t(v.buffers[2].size));
 const char* events[]={"initial","static","static","slow_pan","slow_pan","camera_cut","moving_light","moving_cutout","cutout_translation","generation_reset_only","exposure_change","pause_reset_only"};
 float previousCamera=0;uint64_t accepted=0,rejected=0;std::ofstream records(out/"frames.jsonl");
 for(uint32_t frame=0;frame<12;frame++){
  auto started=std::chrono::steady_clock::now();
  float camera=frame>=3&&frame<=4?float(frame-2)*1.3f/float(v.width):frame>=5?.15f:0.f;
  float light=frame>=6?-.55f:-.35f;
  uint32_t reset=frame==0||frame==5||frame==6||frame==9||frame==11;
  Push p{};p.width=v.width;p.height=v.height;p.tick=frame<7?0:frame;p.zoom=light;p.viewX=camera;p.flags=reset;
  p.base=uint32_t(int(std::round((camera-previousCamera)*float(v.width)/1.3f)));
  v.begin();v.barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  v.startPass(false);vkCmdBindPipeline(v.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,v.graphics);v.push(p);vkCmdDraw(v.cb,6,3,0,0);vkCmdEndRenderPass(v.cb);
  v.transition(v.depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);
  v.copyImage(v.depth,VK_IMAGE_ASPECT_DEPTH_BIT,v.buffers[8]);
  v.transition(v.depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  v.bindCompute(lighting,p,(pixels+63)/64);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  v.bindCompute(temporal,p,(pixels+63)/64);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  v.bindCompute(spatial,p,(pixels+63)/64);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT|VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_SHADER_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);v.submit();
  auto raw=(float*)v.buffers[0].map,acc=(float*)v.buffers[1].map,filtered=(float*)v.buffers[5].map,hist=(float*)v.buffers[2].map;
  // Validate every input/output BEFORE comparison, clamping or integer conversion.
  for(uint32_t i=0;i<pixels;i++){
   unitValue(((float*)v.buffers[8].map)[i]);unitValue(filtered[i]);
   for(int c=0;c<4;c++){unitValue(raw[4*i+c]);unitValue(acc[4*i+c]);unitValue(hist[4*i+c]);}
  }
  // Independent host reference for reproject/reject/clamp and edge-aware filter.
  for(uint32_t i=0;i<pixels;i++){
   int x=int(i%v.width),y=int(i/v.width),previousX=x+int32_t(p.base);
   float weight=0,historyValue=raw[4*i],lo=raw[4*i],hi=raw[4*i];
   if(!reset && previousX>=0 && previousX<int(v.width)){
    uint32_t j=y*v.width+previousX;
    if(std::abs(raw[4*i+1]-hist[4*j+1])<.01f && raw[4*i+2]==hist[4*j+2] && std::abs(raw[4*i]-hist[4*j])<.25f && hist[4*j+3]>0){weight=.8f;historyValue=hist[4*j];}
   }
   float spatialSum=0,spatialWeight=0;
   for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
    uint32_t j=std::clamp(y+dy,0,int(v.height)-1)*v.width+std::clamp(x+dx,0,int(v.width)-1);
    lo=std::min(lo,raw[4*j]);hi=std::max(hi,raw[4*j]);
    if(acc[4*j+2]==acc[4*i+2] && std::abs(acc[4*j+1]-acc[4*i+1])<.01f){float w=std::exp(-float(dx*dx+dy*dy));spatialWeight+=w;spatialSum+=acc[4*j]*w;}
   }
   float expected=raw[4*i]*(1-weight)+std::clamp(historyValue,lo,hi)*weight;
   unitValue(weight);unitValue(historyValue);unitValue(lo);unitValue(hi);unitValue(expected);
   if(!std::isfinite(spatialSum)||!std::isfinite(spatialWeight)||spatialWeight<=0)throw std::runtime_error("Nonfinite CPU oracle intermediate");
   unitValue(spatialSum/spatialWeight);
   if(std::abs(acc[4*i]-expected)>1e-5f || std::abs(acc[4*i+3]-weight)>1e-5f || std::abs(filtered[i]-spatialSum/spatialWeight)>1e-5f)throw std::runtime_error("Temporal/spatial CPU oracle mismatch");
  }
  uint32_t shadowed=0,lit=0,used=0;double delta=0.;
  for(uint32_t i=0;i<pixels;i++){if(!std::isfinite(filtered[i])||filtered[i]<0||filtered[i]>1.00001f)throw std::runtime_error("Nonfinite/out-of-range visibility");shadowed+=raw[4*i]<.5;lit+=raw[4*i]>.9;used+=acc[4*i+3]>0;delta+=std::abs(filtered[i]-raw[4*i]);hist[4*i]=filtered[i];hist[4*i+1]=raw[4*i+1];hist[4*i+2]=raw[4*i+2];hist[4*i+3]=1;}
  if(!shadowed||!lit|| (reset&&used))throw std::runtime_error("Shadow coverage/history reset assertion");
  accepted+=used;rejected+=pixels-used;
  std::string prefix="frame-"+std::to_string(frame);pgm(out/(prefix+"-shadow-depth.pgm"),(float*)v.buffers[8].map,v.width,v.height);pgm(out/(prefix+"-raw.pgm"),raw,v.width,v.height,4);pgm(out/(prefix+"-temporal.pgm"),acc,v.width,v.height,4);pgm(out/(prefix+"-filtered.pgm"),filtered,v.width,v.height);pgm(out/(prefix+"-history-weight.pgm"),acc,v.width,v.height,4,3);pgm(out/(prefix+"-receiver-depth.pgm"),raw,v.width,v.height,4,1);
  float exposure=frame>=10?2.f:1.f;
  for(int mode=0;mode<2;mode++){
   std::ofstream color(out/(prefix+(mode?"-filtered-color.ppm":"-raw-color.ppm")),std::ios::binary);color<<"P6\n"<<v.width<<" "<<v.height<<"\n255\n";
   for(uint32_t i=0;i<pixels;i++)for(int c=0;c<3;c++){
    float visibility=mode?filtered[i]:raw[4*i];float probe[3]={.08f,.12f,.2f};
    float diffuse[3]={.45f,.38f,.28f};bool reflectionPlane=(i/v.width)>v.height*3/4;
    float linear=(reflectionPlane?probe[c]:probe[c]+diffuse[c]*visibility)*exposure;
    uint8_t encoded=uint8_t(std::pow(linear/(1+linear),1.f/2.2f)*255+.5f);color.write((char*)&encoded,1);
   }
  }
  records<<"{\"frame\":"<<frame<<",\"event\":\""<<events[frame]<<"\",\"camera_x\":"<<camera<<",\"light_shear\":"<<light<<",\"exposure\":"<<exposure<<",\"reset\":"<<reset<<",\"accepted_history_pixels\":"<<used<<",\"shadowed_pixels\":"<<shadowed<<",\"lit_pixels\":"<<lit<<",\"temporal_spatial_oracle_mismatches\":0,\"cpu_submit_readback_ms\":"<<std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count()<<",\"filter_raw_mae\":"<<delta/pixels<<"}\n";previousCamera=camera;
 }
 if(!disableQuery&&rq.rayQuery&&as.accelerationStructure&&f12.bufferDeviceAddress&&has(VK_KHR_DEFERRED_HOST_OPERATIONS_EXTENSION_NAME)){QueryRuntime query(v);query.run(argv[1],out);}
 else std::cout<<"{\"query_execution\":\"SKIPPED\",\"forced_baseline\":"<<disableQuery<<"}\n";
 if(!accepted||!rejected||validationErrors)throw std::runtime_error("History coverage/validation failure");
 std::cout<<"{\"baseline\":\"PASS\",\"frames\":12,\"history_accepted\":"<<accepted<<",\"history_rejected\":"<<rejected<<",\"validation_errors\":"<<validationErrors<<",\"mobile_quality\":\"UNVERIFIED\"}\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
