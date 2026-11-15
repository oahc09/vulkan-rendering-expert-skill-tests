// SPDX-License-Identifier: MIT
#include "switch_helper.hpp"
static std::vector<float> readAtlas(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=65*49*16)throw std::runtime_error("atlas size");std::vector<float>v(65*49*4);f.seekg(0);f.read((char*)v.data(),v.size()*4);for(float x:v)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("atlas range");return v;}
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("SHADERS INPUTS NEWOUT");std::filesystem::path inputs=argv[2],out=argv[3];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 TextLab lab(argv[1]);if(!lab.validation)throw std::runtime_error("validation required");auto msdf=readAtlas(inputs/"msdf.rgba32f");
 const float scales[]={.75f,.95f,1.05f,1.15f,1.05f,.95f,.85f,.95f,1.05f,1.15f};
 bool useMsdf=false,negativeExpected=false;std::ofstream events(out/"events.jsonl");
 auto render=[&](int frame,bool choice,const std::string&name){lab.msdfScale=scales[frame];lab.msdfPhase=(frame%4)*.25f;
  auto bitmap=readAtlas(inputs/(std::to_string(frame)+".rgba32f"));
  if(!choice){std::swap(lab.coverage,lab.bitmapCoverage);std::swap(lab.textSet,lab.bitmapSet);std::swap(lab.textPipeline,lab.bitmapPipeline);}
  auto result=lab.draw(choice?msdf:bitmap,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
  if(!choice){std::swap(lab.coverage,lab.bitmapCoverage);std::swap(lab.textSet,lab.bitmapSet);std::swap(lab.textPipeline,lab.bitmapPipeline);}
  auto dir=out/name;std::filesystem::create_directory(dir);save(dir/"color.rgba32f",result[0]);save(dir/"velocity.rgba32f",result[1]);save(dir/"id.rgba32f",result[2]);
 };
 for(int i=0;i<10;i++){bool old=useMsdf;if(scales[i]<=.9f)useMsdf=false;else if(scales[i]>=1.1f)useMsdf=true;
  render(i,useMsdf,std::to_string(i));if(i==2){negativeExpected=useMsdf;render(i,!useMsdf,"wrong-hold");}events<<"{\"frame\":"<<i<<",\"previous\":"<<old<<",\"selected\":"<<useMsdf<<"}\n";
 }
 // Fixed hold frame2: correct prior state is bitmap; wrong MSDF is legal.
 events<<"{\"frame\":2,\"expected\":"<<negativeExpected<<",\"actual\":"<<!negativeExpected<<",\"negative\":true}\n";
 if(validationErrors)throw std::runtime_error("validation");std::cout<<"SWITCH_PASS validation_enabled=1\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
