// SPDX-License-Identifier: MIT
#include "board.hpp"
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("usage SHADERS JOBS NEW_OUTPUT");
 std::filesystem::path root=argv[3];if(!std::filesystem::create_directory(root))throw std::runtime_error("existing output");
 std::ifstream jobs(argv[2]);if(!jobs)throw std::runtime_error("missing jobs");
 {TextLab lab(argv[1]);std::string name,path;int tr,mode,count,colored;float cx,cy;int n=0;
 while(jobs>>name>>path>>tr>>mode>>count>>colored>>cx>>cy){
 if(++n>100||name.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789-")!=std::string::npos||tr<0||tr>5||mode<0||mode>1||count<1||count>16||colored<0||colored>1)throw std::runtime_error("job budget");
 std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in||in.tellg()!=65*49*16*256)throw std::runtime_error("atlas size");
 std::vector<float> pixels(65*49*64*16);in.seekg(0);in.read((char*)pixels.data(),pixels.size()*4);
 lab.transform=tr;lab.mode=mode;lab.layers=count;lab.colored=colored;lab.cx=cx;lab.cy=cy;if(!std::isfinite(cx)||!std::isfinite(cy)||cx<0||cx>65||cy<0||cy>49)throw std::runtime_error("center budget");
 auto r=lab.draw(pixels,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});
 auto dest=root/name;if(!std::filesystem::create_directory(dest))throw std::runtime_error("duplicate job");
 save(dest/"color.rgba32f",r[0]);save(dest/"velocity.rgba32f",r[1]);save(dest/"id.rgba32f",r[2]);
 }
 if(!jobs.eof()||!n)throw std::runtime_error("malformed jobs");
 std::cout<<"validation_enabled="<<lab.validation<<" jobs="<<n<<" vendor="<<lab.properties.vendorID<<" driver="<<lab.properties.driverVersion<<"\n";
 }if(validationErrors)throw std::runtime_error("validation errors");return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
