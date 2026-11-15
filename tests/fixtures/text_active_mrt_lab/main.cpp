// SPDX-License-Identifier: MIT
#include "active_lab_reused.hpp"
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("usage active SHADERS NEW_OUTPUT normal|bad-mask|bad-depth");
 std::string mode=argv[3];if(mode!="normal"&&mode!="bad-mask"&&mode!="bad-depth")throw std::runtime_error("invalid mode");gBadMask=mode=="bad-mask";gBadDepth=mode=="bad-depth";
 std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {TextLab lab(argv[1]);std::vector<float> mask(lab.width*lab.height,.5f);auto result=lab.draw(mask,{.2f,.2f,.2f,1},{1,1,1,.8f});save(out/"color.f32",result[0]);save(out/"velocity.f32",result[1]);save(out/"id.f32",result[2]);std::vector<float> depth(mask.size());std::memcpy(depth.data(),lab.buffers[lab.readDepth].map,depth.size()*4);save(out/"depth.f32",depth);std::cout<<"ACTIVE_MRT_PASS validation_enabled="<<lab.validation<<"\n";}
 if(validationErrors)throw std::runtime_error("validation diagnostics");return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
