// SPDX-License-Identifier: MIT
#include "text_lab_reused.hpp"
struct ExtraPage {TextLab& lab;Image owned;~ExtraPage(){vkDestroyImageView(lab.device,owned.view,nullptr);vkDestroyImage(lab.device,owned.image,nullptr);vkFreeMemory(lab.device,owned.memory,nullptr);}};
int main(int argc,char**argv){try{
 if(argc!=3 && !(argc==4 && std::string(argv[3])=="--abort-pending"))throw std::runtime_error("usage descriptor_lab SHADERS NEW_OUTPUT [--abort-pending]");
 std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {TextLab lab(argv[1]);auto originalPage=lab.coverage;auto originalSet=lab.textSet;
 auto candidate=lab.image(VK_FORMAT_R32_SFLOAT,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);ExtraPage extra{lab,candidate};
 VkDescriptorSet candidateSet{};VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};ai.descriptorPool=lab.textPool;ai.descriptorSetCount=1;ai.pSetLayouts=&lab.textSetLayout;VK(vkAllocateDescriptorSets(lab.device,&ai,&candidateSet));
 VkDescriptorImageInfo ii{lab.sampler,candidate.view,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};VkWriteDescriptorSet wr{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};wr.dstSet=candidateSet;wr.descriptorCount=1;wr.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;wr.pImageInfo=&ii;vkUpdateDescriptorSets(lab.device,1,&wr,0,nullptr);
 if(candidateSet==originalSet || candidate.image==originalPage.image)throw std::runtime_error("distinct descriptors/pages missing");
 for(int generation=0;generation<2;generation++){
  if(generation){ // previous actual fence retired; never update the old set.
   lab.coverage=candidate;lab.textSet=candidateSet;extra.owned=originalPage;
  }
  lab.descriptorIdentity=generation;lab.injectFailure=(argc==4);
  std::vector<float> mask(lab.width*lab.height);
  for(unsigned y=0;y<lab.height;y++)for(unsigned x=0;x<lab.width;x++)mask[y*lab.width+x]=generation?float((x+2*y)%5)/4.f:float((x+y)%3)/2.f;
  auto pixels=lab.draw(mask,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
  auto folder=out/("generation-"+std::to_string(generation));std::filesystem::create_directory(folder);save(folder/"mask.f32",mask);save(folder/"color.rgba32f",pixels[0]);save(folder/"velocity.rgba32f",pixels[1]);save(folder/"id.rgba32f",pixels[2]);
 }
 std::ofstream n(out/"numerics.json");n<<"{\"distinct_pages\":2,\"distinct_descriptor_sets\":2,\"pending_draws\":2,\"retired_draws\":2,\"validation_enabled\":"<<(lab.validation?"true":"false")<<"}\n";
 }
 if(validationErrors)throw std::runtime_error("validation diagnostics");std::cout<<"DESCRIPTOR_RESOURCES_DESTROYED\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
