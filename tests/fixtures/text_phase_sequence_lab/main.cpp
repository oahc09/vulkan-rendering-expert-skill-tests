// SPDX-License-Identifier: MIT
#include "switch_helper.hpp"
static std::vector<float> readAtlas(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=65*49*16)throw std::runtime_error("atlas size");std::vector<float>v(65*49*4);f.seekg(0);f.read((char*)v.data(),v.size()*4);for(float x:v)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("atlas range");return v;}
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("SHADERS INPUTS NEWOUT");std::filesystem::path inputs=argv[2],out=argv[3];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 TextLab lab(argv[1]);if(!lab.validation)throw std::runtime_error("validation required");auto msdf=readAtlas(inputs/"msdf.rgba32f");bool state=false,negativeExpected=false;std::ofstream events(out/"events.jsonl");
 auto route=[&](float scale){if(scale<=.9f)state=false;else if(scale>=1.1f)state=true;return state;};
 auto render=[&](float scale,float phase,bool choice,const std::string&input,const std::string&name){lab.msdfScale=scale;lab.msdfPhase=phase;auto bitmap=readAtlas(inputs/(input+".rgba32f"));
  if(!choice){std::swap(lab.coverage,lab.bitmapCoverage);std::swap(lab.textSet,lab.bitmapSet);std::swap(lab.textPipeline,lab.bitmapPipeline);}
  auto result=lab.draw(choice?msdf:bitmap,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
  if(!choice){std::swap(lab.coverage,lab.bitmapCoverage);std::swap(lab.textSet,lab.bitmapSet);std::swap(lab.textPipeline,lab.bitmapPipeline);}
  auto dir=out/name;if(!std::filesystem::create_directory(dir))throw std::runtime_error("duplicate frame");save(dir/"color.rgba32f",result[0]);save(dir/"velocity.rgba32f",result[1]);save(dir/"id.rgba32f",result[2]);
 };
 for(int branch=0;branch<2;branch++){
  float prime=branch?1.15f:.85f;bool selected=route(prime);render(prime,0,selected,"warm"+std::to_string(branch),"warm"+std::to_string(branch));events<<"{\"kind\":\"warmup\",\"branch\":"<<branch<<",\"selected\":"<<selected<<"}\n";
  for(int frame=0;frame<17;frame++){
   float phase=frame/16.f;bool old=state;selected=route(1.05f);render(1.05f,phase,selected,std::to_string(frame),std::to_string(branch)+"-"+std::to_string(frame));
   events<<"{\"kind\":\"measured\",\"branch\":"<<branch<<",\"frame\":"<<frame<<",\"previous\":"<<old<<",\"selected\":"<<selected<<"}\n";
   if(branch==0&&frame==8){negativeExpected=state;render(1.05f,phase,!state,std::to_string(frame),"wrong-hold");}
  }
 }
 events<<"{\"kind\":\"negative\",\"branch\":0,\"frame\":8,\"expected\":"<<negativeExpected<<",\"actual\":"<<!negativeExpected<<"}\n";
 if(validationErrors)throw std::runtime_error("validation");std::cout<<"PHASE_SEQUENCE_PASS validation_enabled=1\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
