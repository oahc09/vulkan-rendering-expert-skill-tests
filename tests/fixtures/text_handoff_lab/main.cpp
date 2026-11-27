// SPDX-License-Identifier: MIT
#include "handoff.hpp"
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("SHADERS NEWOUT MODE");std::filesystem::path out=argv[2];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");gMode=argv[3];
 if(gMode!="normal"&&gMode!="pipeline"&&gMode!="descriptor"&&gMode!="vertex"&&gMode!="viewport"&&gMode!="scissor"&&gMode!="all")throw std::runtime_error("mode");
 TextLab lab(argv[1]);if(!lab.validation)throw std::runtime_error("validation required");std::vector<float> mask(65*49);
 for(int y=0;y<49;y++)for(int x=0;x<65;x++)mask[y*65+x]=(x>=6&&x<59&&y>=5&&y<44&&!(x>=22&&x<43&&y>=17&&y<32))?.5f:0.f;
 auto result=lab.draw(mask,{.1,.2,.3,1},{.9,.5,.2,.75});for(int i=0;i<3;i++)save(out/(std::string(i==0?"color":i==1?"velocity":"id")+".f32"),result[i]);
 if(validationErrors)throw std::runtime_error("validation");std::cout<<"HANDOFF_PASS validation_enabled=1 draws=3 renderpasses=1 submissions=1\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
