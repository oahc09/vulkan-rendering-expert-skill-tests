#version 450
#extension GL_GOOGLE_include_directive : require
#define READ_ONLY
#include "sim.glsl"
layout(location=0) out vec4 color;
void main(){uint corners[6]=uint[](0,1,2,0,2,3);uint c=corners[gl_VertexIndex%6];
 if(p.mode==2){uint cell=uint(gl_VertexIndex)/6u,x=cell%(p.width-1),y=cell/(p.width-1);uint i=(y+(c>=2?1u:0u))*p.width+x+(c==1||c==2?1u:0u);
 vec2 xy=vec2(float(i%p.width)/float(p.width-1),float(i/p.width)/float(p.height-1))*1.6-.8;
 gl_Position=vec4(xy+vec2(p.zoom,0),.5+source[i].x.x*.2,1);color=vec4(.15+abs(source[i].x.x)*8.,.3+normal[i].z*.3,.65,1);
 }else{uint i=uint(gl_InstanceIndex);vec2 q=vec2(c==1||c==2?1:-1,c>=2?1:-1)*.015;
 gl_Position=vec4(source[i].x.xy+q+vec2(p.zoom,0),.5+source[i].x.z*.2,1);color=vec4(source[i].x.w==0?1:.2,.7,.3+normal[i].z*.2,1);}
}
