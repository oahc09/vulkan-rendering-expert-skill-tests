// SPDX-License-Identifier: MIT
#include "quad_lab_reused.hpp"
static std::vector<float> read(const char* path,size_t limit){std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("input missing");auto bytes=f.tellg();if(bytes<=0||bytes%4||size_t(bytes)>limit)throw std::runtime_error("input size");std::vector<float>a(size_t(bytes)/4);f.seekg(0);f.read(reinterpret_cast<char*>(a.data()),bytes);for(float v:a)if(!std::isfinite(v))throw std::runtime_error("nonfinite input");return a;}
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("usage quad_lab SHADERS ATLAS VERTICES NEW_OUTPUT");
 auto atlas=read(argv[2],65*49*4),verts=read(argv[3],32768);
 if(atlas.size()!=65*49||verts.size()%24||verts.size()/4>1536)throw std::runtime_error("invalid dimensions");
 for(float v:atlas)if(v<0||v>1)throw std::runtime_error("invalid coverage");
 for(size_t i=0;i<verts.size();i+=4)if(std::abs(verts[i])>4||std::abs(verts[i+1])>4||verts[i+2]<0||verts[i+2]>1||verts[i+3]<0||verts[i+3]>1)throw std::runtime_error("invalid vertex bounds");
 std::filesystem::path out=argv[4];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {TextLab lab(argv[1]);lab.quadBuffer=lab.buffers.size();lab.buffers.push_back(lab.buffer(verts.size()*4,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT));std::memcpy(lab.buffers[lab.quadBuffer].map,verts.data(),verts.size()*4);lab.quadCount=verts.size()/4;
 auto result=lab.draw(atlas,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});save(out/"color.rgba32f",result[0]);save(out/"velocity.rgba32f",result[1]);save(out/"id.rgba32f",result[2]);std::cout<<"QUAD_PASS validation_enabled="<<lab.validation<<" vertices="<<lab.quadCount<<"\n";}
 if(validationErrors)throw std::runtime_error("validation diagnostics");return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
