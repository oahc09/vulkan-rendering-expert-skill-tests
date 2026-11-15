// SPDX-License-Identifier: MIT
// Build generates the reused header from the unchanged TextLab source.
#include "text_lab_reused.hpp"
int main(int argc,char**argv){try{
  if(argc!=4)throw std::runtime_error("usage: bitmap_lab SHADERS MASK NEW_OUTPUT");
  std::ifstream input(argv[2],std::ios::binary|std::ios::ate);
  if(!input || input.tellg()!=65*49*4)throw std::runtime_error("invalid mask byte size");
  input.seekg(0);std::vector<float> mask(65*49);input.read(reinterpret_cast<char*>(mask.data()),65*49*4);
  for(float x:mask)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("invalid mask coverage");
  std::filesystem::path out=argv[3];if(!std::filesystem::create_directory(out))throw std::runtime_error("refuse existing output");
  TextLab lab(argv[1]);auto pixels=lab.draw(mask,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
  save(out/"color.rgba32f",pixels[0]);save(out/"velocity.rgba32f",pixels[1]);save(out/"id.rgba32f",pixels[2]);
  if(validationErrors)throw std::runtime_error("validation errors");
  std::cout<<"BITMAP_GPU_PASS validation_enabled="<<lab.validation<<"\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
