// SPDX-License-Identifier: MIT
// Small authored adapter. msdfgen core is an external, pinned local dependency.
#include "msdfgen.h"
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc,char **argv){try{
 if(argc!=3)throw std::runtime_error("usage generate OUTLINE NEW_RGBA32F");
 std::ifstream in(argv[1]);unsigned contours=0;in>>contours;
 if(!in||contours==0||contours>64)throw std::runtime_error("contour budget");
 msdfgen::Shape shape;size_t total=0;
 for(unsigned i=0;i<contours;i++){
  unsigned edges;in>>edges;if(!in||!edges||edges>2048||total+edges>4096)throw std::runtime_error("edge budget");total+=edges;
  auto &c=shape.addContour();
  for(unsigned j=0;j<edges;j++){
   unsigned n;in>>n;if(n<2||n>4)throw std::runtime_error("edge degree");
   msdfgen::Point2 p[4];for(unsigned k=0;k<n;k++){in>>p[k].x>>p[k].y;if(!in||!std::isfinite(p[k].x)||!std::isfinite(p[k].y)||std::abs(p[k].x)>256||std::abs(p[k].y)>256)throw std::runtime_error("coordinate budget");}
   if(n==2)c.addEdge(msdfgen::EdgeHolder(p[0],p[1]));
   else if(n==3)c.addEdge(msdfgen::EdgeHolder(p[0],p[1],p[2]));
   else c.addEdge(msdfgen::EdgeHolder(p[0],p[1],p[2],p[3]));
  }
 }
 in>>std::ws;if(!in.eof())throw std::runtime_error("trailing input");
 if(!shape.validate())throw std::runtime_error("invalid contour closure");
 shape.normalize();shape.orientContours();msdfgen::edgeColoringSimple(shape,3.0,0);
 msdfgen::Bitmap<float,3> bitmap(65,49);
 msdfgen::generateMSDF(bitmap,shape,msdfgen::Projection(msdfgen::Vector2(1.),msdfgen::Vector2(0.)),msdfgen::Range(4.));
 if(std::ifstream(argv[2]).good())throw std::runtime_error("refuse existing output");
 std::ofstream out(argv[2],std::ios::binary);size_t different=0;
 for(int y=0;y<49;y++)for(int x=0;x<65;x++){
  const float *p=bitmap(x,y);float rgba[4];for(int c=0;c<3;c++){if(!std::isfinite(p[c]))throw std::runtime_error("nonfinite MSDF");rgba[c]=std::max(0.f,std::min(1.f,p[c]));}rgba[3]=1;
  if(std::abs(rgba[0]-rgba[1])>1e-4||std::abs(rgba[1]-rgba[2])>1e-4)different++;
  out.write(reinterpret_cast<char*>(rgba),sizeof(rgba));
 }
 if(!out)throw std::runtime_error("output write");
 std::cout<<"edge_coloring=Simple seed=0 angle=3 px_range=4 channels=RGB distinct_pixels="<<different<<"\n";
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
