#include "shadow_reused.hpp"
struct Scene:Shadow{
 VkDescriptorPool labelPool{};
 Scene(const std::string&dir,const std::vector<float>&mesh,const std::vector<float>&mask):Shadow(dir,mesh){
 casterVB=vb;casterCount=mesh.size()/6;
 std::vector<float>v;auto quad=[&](float x0,float y0,float x1,float y1,float z){for(auto p:std::vector<std::array<float,2>>{{x0,y0},{x1,y0},{x0,y1},{x0,y1},{x1,y0},{x1,y1}})v.insert(v.end(),{p[0],p[1],z,0,0,0});};
 quad(-20,-20,85,70,10);quad(34,17,43,28,1);quad(32,15,46,30,3);
 sceneVB=buffers.size();buffers.push_back(buffer(v.size()*4,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT));memcpy(buffers[sceneVB].map,v.data(),v.size()*4);
 VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1};VkDescriptorPoolCreateInfo dp{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dp.maxSets=1;dp.poolSizeCount=1;dp.pPoolSizes=&size;VK(vkCreateDescriptorPool(device,&dp,nullptr,&labelPool));VkDescriptorSetAllocateInfo sa{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};sa.descriptorPool=labelPool;sa.descriptorSetCount=1;sa.pSetLayouts=&textSetLayout;VK(vkAllocateDescriptorSets(device,&sa,&labelSet));VkDescriptorImageInfo info{sampler,coverage.view,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};VkWriteDescriptorSet wr{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};wr.dstSet=labelSet;wr.descriptorCount=1;wr.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;wr.pImageInfo=&info;vkUpdateDescriptorSets(device,1,&wr,0,nullptr);
 }
 ~Scene(){vkDeviceWaitIdle(device);vkDestroyDescriptorPool(device,labelPool,nullptr);}
};
std::vector<float>read(const char*p,size_t cap){std::ifstream f(p,std::ios::binary|std::ios::ate);auto n=f.tellg();if(n<=0||n%4||n>std::streamoff(cap))throw std::runtime_error("size");std::vector<float>v(n/4);f.seekg(0);f.read((char*)v.data(),n);for(float a:v)if(!std::isfinite(a))throw std::runtime_error("finite");return v;}
int main(int argc,char**argv){try{if(argc!=5)throw std::runtime_error("shaders mesh mask out");auto mesh=read(argv[2],100000),mask=read(argv[3],12740);if(mesh.size()%18||mask.size()!=3185)throw std::runtime_error("input dimensions");std::filesystem::path out=argv[4];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {Scene s(argv[1],mesh,mask);if(!s.validation)throw std::runtime_error("validation required");std::cout<<"validation_enabled=1\n";
 const char*names[]={"A","B","B-no-shadow","B-stale-label"};for(int i=0;i<4;i++){s.cameraX=i?-.25f:.25f;s.cameraY=i?.25f:.125f;s.bypass=i==2;s.stale=i==3;auto r=s.draw(mask,{0,0,0,1},{0,0,0,0});auto d=out/names[i];std::filesystem::create_directory(d);save(d/"color.f32",r[0]);save(d/"velocity.f32",r[1]);save(d/"id.f32",r[2]);std::vector<float>depth(3185);memcpy(depth.data(),s.buffers[s.readDepth].map,12740);save(d/"depth.f32",depth);}
 s.readShadow();std::vector<float>d(3185);memcpy(d.data(),s.buffers[s.readMap].map,12740);save(out/"shadow.f32",d);}
 if(validationErrors)throw std::runtime_error("validation failed");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
