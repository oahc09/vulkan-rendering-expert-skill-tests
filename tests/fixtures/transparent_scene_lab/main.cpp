// SPDX-License-Identifier: MIT
#define main engine_scale_lab_original_main
#include "../engine_scale_lab/main.cpp"
#undef main
#include <iomanip>
struct Splat {float center[4],shape[4],color[4];uint32_t identity[4];};
static_assert(sizeof(Splat)==64,"std430 ABI");
static float half(uint16_t h){unsigned e=(h>>10)&31,m=h&1023;float x=e==0?std::ldexp(float(m),-24):e==31?(m?NAN:INFINITY):std::ldexp(float(1024+m),int(e)-25);return h&32768?-x:x;}
struct Lab:Vulkan{
 VkFormat format;VkPipeline opaqueLab,alphaLab,accumLab,revealLab;size_t readback;
 Lab(std::string shaders):Vulkan(65*49,shaders,true){}
 #include "pipeline.hpp"
 bool supported(VkFormat f){VkFormatProperties p;vkGetPhysicalDeviceFormatProperties(physical,f,&p);VkFormatFeatureFlags need=VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT|VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT;return (p.optimalTilingFeatures&need)==need;}
 void target(VkFormat f){
  format=f;vkDestroyFramebuffer(device,framebuffer,nullptr);vkDestroyRenderPass(device,clearPass,nullptr);vkDestroyRenderPass(device,loadPass,nullptr);
  vkDestroyImageView(device,color.view,nullptr);vkDestroyImage(device,color.image,nullptr);vkFreeMemory(device,color.memory,nullptr);
  color=image(f,VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
  clearPass=labPass(f);loadPass=labPass(f);VkImageView views[]={color.view,depth.view};
  VkFramebufferCreateInfo fb{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};fb.renderPass=clearPass;fb.attachmentCount=2;fb.pAttachments=views;fb.width=width;fb.height=height;fb.layers=1;VK(vkCreateFramebuffer(device,&fb,nullptr,&framebuffer));
  readback=buffers.size();buffers.push_back(buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_DST_BIT));
  opaqueLab=labPipeline(0);alphaLab=labPipeline(2);accumLab=labPipeline(1);revealLab=labPipeline(3);
 }
 std::vector<float> render(std::vector<Splat> splats,uint32_t mode,float camera,bool mesh){
  if(splats.size()>128)throw std::runtime_error("OVERFLOW: reject frame before upload (capacity=128)");
  Splat wall{{-.55f,0,.25f,0},{.18f,.9f,0,0},{.15f,.2f,.25f,1},{9,0,1,0}};
  if(mesh)splats.insert(splats.begin(),wall);
  std::memcpy(buffers[0].map,splats.data(),splats.size()*sizeof(Splat));
  begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  VkClearValue clear[2]{};for(float &c:clear[0].color.float32)c=mode==2?1:0;clear[1].depthStencil.depth=1;
  VkRenderPassBeginInfo rp{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};rp.renderPass=clearPass;rp.framebuffer=framebuffer;rp.renderArea={{0,0},{width,height}};rp.clearValueCount=2;rp.pClearValues=clear;
  vkCmdBeginRenderPass(cb,&rp,VK_SUBPASS_CONTENTS_INLINE);vkCmdBindDescriptorSets(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,layout,0,1,&set,0,nullptr);
  Push p{};p.width=width;p.height=height;p.mode=mode;p.viewX=camera;
  if(mesh){vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,opaqueLab);push(p);vkCmdDraw(cb,6,1,0,0);p.base=1;}
  vkCmdBindPipeline(cb,VK_PIPELINE_BIND_POINT_GRAPHICS,mode==1?accumLab:mode==2?revealLab:mode==3?opaqueLab:alphaLab);push(p);vkCmdDraw(cb,6,uint32_t(splats.size())-p.base,0,0);vkCmdEndRenderPass(cb);
  transition(color,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);copyImage(color,VK_IMAGE_ASPECT_COLOR_BIT,buffers[readback]);
  transition(depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);copyImage(depth,VK_IMAGE_ASPECT_DEPTH_BIT,buffers[8]);
  transition(depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);submit();
  std::vector<float> result(width*height*4);for(size_t i=0;i<result.size();i++){result[i]=format==VK_FORMAT_R8G8B8A8_UNORM?((uint8_t*)buffers[readback].map)[i]/255.f:format==VK_FORMAT_R16G16B16A16_SFLOAT?half(((uint16_t*)buffers[readback].map)[i]):((float*)buffers[readback].map)[i];if(!std::isfinite(result[i]))throw std::runtime_error("Nonfinite render");}return result;
 }
};
static void save(const std::filesystem::path&p,const std::vector<float>&a){std::ofstream f(p,std::ios::binary);f.write((char*)a.data(),a.size()*4);}
static std::vector<Splat> scene(){return {{{0,0,.7f,0},{.85f,.75f,0,0},{0,0,1,.5f},{1,0,1,0}},{{0,0,.3f,0},{.85f,.75f,0,0},{1,0,0,.5f},{2,0,1,0}}};}
static double alphaAt(const Splat&s,double x,double y,float camera){double qx=(x-s.center[0]-camera)/s.shape[0],qy=(y-s.center[1])/s.shape[1];if(std::abs(qx)>1||std::abs(qy)>1)return 0;double r=qx*qx+qy*qy;if(s.identity[3]&&r>1)return 0;return s.color[3]*(s.identity[3]?std::exp(-4.5*r):1);}
static double compare(const std::vector<float>&a,const std::vector<double>&b,double tolerance){double worst=0;size_t worstIndex=0;for(size_t i=0;i<a.size();i++){if(!std::isfinite(a[i])||!std::isfinite(b[i]))throw std::runtime_error("Nonfinite oracle");if(std::abs(a[i]-b[i])>worst){worst=std::abs(a[i]-b[i]);worstIndex=i;}}if(worst>tolerance)throw std::runtime_error("Oracle mismatch: "+std::to_string(worst)+" > "+std::to_string(tolerance)+" at "+std::to_string(worstIndex)+" actual "+std::to_string(a[worstIndex])+" expected "+std::to_string(b[worstIndex]));return worst;}
static std::vector<double> oracle(const std::vector<Splat>&s,float camera,bool mesh,uint32_t mode=0){std::vector<double> a(65*49*4);for(int y=0;y<49;y++)for(int x=0;x<65;x++){size_t i=(y*65+x)*4;double px=2.*(x+.5)/65-1,py=2.*(y+.5)/49-1;bool wall=mesh&&std::abs(px+.55-camera)<.18&&std::abs(py)<.9;double depth=wall?.25:1;double color[]={.15,.2,.25,1};if(wall)for(int c=0;c<4;c++)a[i+c]=mode==3?(c==0?9:c==1?0:c==2?1:.25):color[c];for(auto &v:s){double al=alphaAt(v,px,py,camera);if(v.center[2]>depth||al==0)continue;if(mode==3){if(al<.01)continue;depth=v.center[2];for(int c=0;c<4;c++)a[i+c]=c==3?depth:v.identity[c];}else{for(int c=0;c<3;c++)a[i+c]=v.color[c]*al+(1-al)*a[i+c];a[i+3]=al+(1-al)*a[i+3];}}}return a;}
int main(int argc,char**argv){try{
 if(argc<3)throw std::runtime_error("usage: transparent_scene_lab SHADER_DIR NEW_OUTPUT_DIR [--disable-wboit] [--overflow] [--asset BINARY]");
 bool disable=false,overflow=false;std::string asset;
 for(int i=3;i<argc;i++){std::string arg=argv[i];if(arg=="--disable-wboit")disable=true;else if(arg=="--overflow")overflow=true;else if(arg=="--asset"&&i+1<argc)asset=argv[++i];else throw std::runtime_error("Unknown option");}
 std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("Refuse existing output directory");
 Lab v(argv[1]);std::ofstream report(out/"frames.jsonl");
 VkPhysicalDeviceDriverProperties driver{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRIVER_PROPERTIES};VkPhysicalDeviceProperties2 props{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2};props.pNext=&driver;vkGetPhysicalDeviceProperties2(v.physical,&props);
 auto quoted=[](const char* raw){std::string s="\"";for(const unsigned char* p=(const unsigned char*)raw;*p;p++){if(*p=='"'||*p=='\\')s+='\\';if(*p>=32)s+=char(*p);}return s+"\"";};
 std::cout<<"{\"driverVersion\":"<<props.properties.driverVersion<<",\"vendorID\":"<<props.properties.vendorID<<",\"deviceID\":"<<props.properties.deviceID<<",\"driverID\":"<<driver.driverID<<",\"driverName\":"<<quoted(driver.driverName)<<",\"driverInfo\":"<<quoted(driver.driverInfo)<<"}\n";

 VkPhysicalDeviceFeatures features;vkGetPhysicalDeviceFeatures(v.physical,&features);std::cout<<"{\"independentBlend\":"<<features.independentBlend<<",\"wboit_path\":\"two_single_attachment_passes_no_independentBlend_needed\"}\n";
 if(overflow){v.target(VK_FORMAT_R8G8B8A8_UNORM);v.render(std::vector<Splat>(129),0,0,false);throw std::runtime_error("Overflow unexpectedly accepted");}
 for(auto format:{VK_FORMAT_R8G8B8A8_UNORM,VK_FORMAT_R16G16B16A16_SFLOAT,VK_FORMAT_R32G32B32A32_SFLOAT}){
  if(!v.supported(format)){report<<"{\"format\":"<<format<<",\"status\":\"SKIPPED_FORMAT_CAPABILITY\"}\n";continue;}v.target(format);double tolerance=format==VK_FORMAT_R8G8B8A8_UNORM?.009:format==VK_FORMAT_R16G16B16A16_SFLOAT?.003:1e-5;
  for(int frame=0;frame<4;frame++){auto s=scene();if(frame==1){s[0].center[2]=.3f;s[1].center[2]=.7f;}if(frame>=2)for(auto &g:s)g.identity[3]=1;
   std::stable_sort(s.begin(),s.end(),[](auto&a,auto&b){if(a.center[2]!=b.center[2])return a.center[2]>b.center[2];return a.identity[0]<b.identity[0];});float camera=frame==3?.14f:0;bool mesh=frame>=2;
   auto a=v.render(s,0,camera,mesh);double err=compare(a,oracle(s,camera,mesh),tolerance);std::string name="format-"+std::to_string(format)+"-frame-"+std::to_string(frame);save(out/(name+".rgba32f"),a);
   uint64_t coverage=0,layerSum=0;for(int y=0;y<49;y++)for(int x=0;x<65;x++){int layers=0;for(auto&g:s)layers+=alphaAt(g,2.*(x+.5)/65-1,2.*(y+.5)/49-1,camera)>0;coverage+=layers>0;layerSum+=layers;}
   report<<"{\"format\":"<<format<<",\"frame\":"<<frame<<",\"camera_x\":"<<camera<<",\"max_error\":"<<err<<",\"tolerance\":"<<tolerance<<",\"estimated_covered_pixels\":"<<coverage<<",\"estimated_layer_sum\":"<<layerSum<<",\"status\":\"PASS\"}\n";
   if(format==VK_FORMAT_R32G32B32A32_SFLOAT&&frame>=2){auto pick=v.render(s,3,camera,true);compare(pick,oracle(s,camera,true,3),1e-5);save(out/(name+"-set-local-generation-depth.rgba32f"),pick);}
  }
  if(format==VK_FORMAT_R32G32B32A32_SFLOAT){for(uint32_t layers:{2u,8u,32u,128u}){std::vector<Splat> low(layers);for(uint32_t i=0;i<layers;i++){low[i]=scene()[1];low[i].center[2]=.9f-.8f*float(i)/float(layers);low[i].color[3]=.01f;low[i].identity[1]=i;}auto a=v.render(low,0,0,false);double err=compare(a,oracle(low,0,false),1e-5);save(out/("low-alpha-"+std::to_string(layers)+".rgba32f"),a);report<<"{\"low_alpha_layers\":"<<layers<<",\"opacity\":0.01,\"max_error\":"<<err<<",\"status\":\"PASS\"}\n";}}
  if(format!=VK_FORMAT_R8G8B8A8_UNORM&&!disable){auto s=scene();auto accum=v.render(s,1,0,false),reveal=v.render(s,2,0,false);std::memcpy(v.buffers[0].map,accum.data(),accum.size()*4);std::memcpy(v.buffers[1].map,reveal.data(),reveal.size()*4);auto resolve=v.compute("resolve.comp");Push rp{};rp.width=v.width;rp.height=v.height;v.begin();v.barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);v.bindCompute(resolve,rp,(v.width*v.height+63)/64);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);v.submit();std::vector<float> resolved(accum.size());std::memcpy(resolved.data(),v.buffers[2].map,resolved.size()*4);for(size_t i=0;i<accum.size();i+=4){double expectedA=accum[i+3]>0?.75:0;if(std::abs(resolved[i+3]-expectedA)>tolerance)throw std::runtime_error("Revealage oracle mismatch");if(expectedA&&(std::abs(resolved[i]-.375)>tolerance||std::abs(resolved[i+2]-.375)>tolerance))throw std::runtime_error("WBOIT resolve mismatch");}save(out/("wboit-"+std::to_string(format)+".rgba32f"),resolved);report<<"{\"format\":"<<format<<",\"wboit\":\"PASS_RASTER_COMPUTE_RESOLVE_HOST_TRANSFER\",\"exact_sorted_max_difference\":0.125}\n";}
 }
 if(disable)report<<"{\"wboit\":\"SKIPPED_FORCED_SORTED_FALLBACK\"}\n";
 // Stable opaque scene snapshot, read back then uploaded to distinct immutable SSBO.
 if(v.supported(VK_FORMAT_R32G32B32A32_SFLOAT)){
  v.target(VK_FORMAT_R32G32B32A32_SFLOAT);auto snapshot=v.render({},0,0,true);std::memcpy(v.buffers[1].map,snapshot.data(),snapshot.size()*4);auto effect=v.compute("effects.comp");
  for(uint32_t steps:{8u,16u}){Push p{};p.width=v.width;p.height=v.height;p.n=steps;v.begin();v.barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);v.bindCompute(effect,p,(v.width*v.height+63)/64);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);v.submit();std::vector<float>a(snapshot.size());std::memcpy(a.data(),v.buffers[2].map,a.size()*4);std::vector<double> expected(a.size());for(uint32_t i=0;i<v.width*v.height;i++){uint32_t x=i%v.width,j=x+3>=v.width?i:i+3;double depth=((float*)v.buffers[8].map)[i]*10.;if(std::abs(((float*)v.buffers[8].map)[j]*10.-depth)>.01)j=i;double front=std::max(0.,std::min(3.,depth)-2.),back=std::max(0.,std::min(6.,depth)-3.),Tf=std::exp(-.35*front),Tb=std::exp(-.35*back),soft=std::clamp((depth-3.)/1.5,0.,1.)*.2;for(int c=0;c<3;c++)expected[4*i+c]=(.2+.1*c)*(1-Tf)+Tf*(.7*soft+(1-soft)*((.2+.1*c)*(1-Tb)+Tb*snapshot[4*j+c]));expected[4*i+3]=Tf*Tb;}double err=compare(a,expected,2e-6);save(out/("effects-"+std::to_string(steps)+".rgba32f"),a);report<<"{\"effects_steps\":"<<steps<<",\"max_error\":"<<err<<",\"status\":\"PASS\"}\n";}
 }
 if(!asset.empty()&&v.supported(VK_FORMAT_R32G32B32A32_SFLOAT)){
  std::ifstream f(asset,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("Missing asset");size_t bytes=f.tellg();if(bytes==0||bytes%sizeof(Splat)||bytes/sizeof(Splat)>128)throw std::runtime_error("Invalid asset capacity");std::vector<Splat> splats(bytes/sizeof(Splat));f.seekg(0);f.read((char*)splats.data(),bytes);if(!f)throw std::runtime_error("Short asset read");
  for(auto&g:splats){for(float x:g.center)if(!std::isfinite(x))throw std::runtime_error("Invalid center");for(float x:g.shape)if(!std::isfinite(x))throw std::runtime_error("Invalid shape");for(float x:g.color)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("Invalid color/opacity");if(g.shape[0]<=0||g.shape[1]<=0||g.center[2]<.01||g.center[2]>1)throw std::runtime_error("Invalid covariance/near plane");}
  std::stable_sort(splats.begin(),splats.end(),[](auto&a,auto&b){if(a.center[2]!=b.center[2])return a.center[2]>b.center[2];return std::lexicographical_compare(a.identity,a.identity+3,b.identity,b.identity+3);});v.target(VK_FORMAT_R32G32B32A32_SFLOAT);
  for(int scale=1;scale<=2;scale++){auto input=splats;for(auto &g:input){g.shape[0]*=scale;g.shape[1]*=scale;}for(int view=0;view<2;view++){float camera=view*.14f;auto a=v.render(input,0,camera,true);double error=compare(a,oracle(input,camera,true),1e-5);save(out/("generated-scale-"+std::to_string(scale)+"-view-"+std::to_string(view)+".rgba32f"),a);uint64_t layers=0,unique=0;double clippedQuad=0,ellipse=0;for(auto&g:input){double x0=std::max(-1.,double(g.center[0]+camera-g.shape[0]-2.f/65)),x1=std::min(1.,double(g.center[0]+camera+g.shape[0]+2.f/65)),y0=std::max(-1.,double(g.center[1]-g.shape[1]-2.f/49)),y1=std::min(1.,double(g.center[1]+g.shape[1]+2.f/49));clippedQuad+=std::max(0.,x1-x0)*std::max(0.,y1-y0)*65*49/4;ellipse+=3.141592653589793*g.shape[0]*g.shape[1]*65*49/4;}for(int y=0;y<49;y++)for(int x=0;x<65;x++){int n=0;for(auto&g:input)n+=alphaAt(g,2.*(x+.5)/65-1,2.*(y+.5)/49-1,camera)>0;layers+=n;unique+=n>0;}report<<"{\"generated_count\":"<<input.size()<<",\"footprint_multiplier\":"<<scale<<",\"view\":"<<view<<",\"clipped_quad_area_estimate\":"<<clippedQuad<<",\"unclipped_ellipse_area_estimate\":"<<ellipse<<",\"covered_pixels_estimate\":"<<unique<<",\"layer_sum_estimate\":"<<layers<<",\"max_error\":"<<error<<",\"status\":\"PASS\"}\n";}}
 }
 if(validationErrors)throw std::runtime_error("Vulkan validation errors");
 std::cout<<"{\"integration\":\"PASS\",\"validation_errors\":"<<validationErrors<<",\"mobile_visual\":\"UNVERIFIED\",\"performance\":\"UNMEASURED\"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
