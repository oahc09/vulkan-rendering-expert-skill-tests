// SPDX-License-Identifier: MIT
#include "msdf_lab_reused.hpp"
int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("usage msdf_lab SHADERS ATLAS SCALE PHASE RANGE NEW_OUTPUT");
 std::ifstream in(argv[2],std::ios::binary|std::ios::ate);
 if(!in||in.tellg()!=65*49*16)throw std::runtime_error("atlas bytes");
 std::vector<float> atlas(65*49*4);in.seekg(0);in.read(reinterpret_cast<char*>(atlas.data()),atlas.size()*4);
 for(float f:atlas)if(!std::isfinite(f)||f<0||f>1)throw std::runtime_error("atlas finite range");
 float scale=std::stof(argv[3]),phase=std::stof(argv[4]),range=std::stof(argv[5]);
 if(!std::isfinite(scale)||scale<.5||scale>1.5||!std::isfinite(phase)||std::abs(phase)>1||!std::isfinite(range)||range<1||range>8)throw std::runtime_error("transform budget");
 std::filesystem::path out=argv[6];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {TextLab lab(argv[1]);lab.msdfScale=scale;lab.msdfPhase=phase;lab.msdfRange=range;
 auto result=lab.draw(atlas,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
 save(out/"color.rgba32f",result[0]);save(out/"velocity.rgba32f",result[1]);save(out/"id.rgba32f",result[2]);
 std::cout<<"MSDF_PASS validation_enabled="<<lab.validation<<" vendor="<<lab.properties.vendorID<<" driver="<<lab.properties.driverVersion<<"\n";}
 if(validationErrors)throw std::runtime_error("validation diagnostics");return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
