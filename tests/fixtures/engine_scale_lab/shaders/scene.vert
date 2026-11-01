#version 450
#extension GL_GOOGLE_include_directive : require
#define VERTEX_READONLY
#include "common.glsl"
layout(location=0) out vec4 color;
void main(){
 if(p.mode==3u){ // trusted opaque wall, with an uncovered half-screen; current frame only
  vec2 v[6]=vec2[](vec2(-1,-1),vec2(0,-1),vec2(0,1),vec2(-1,-1),vec2(0,1),vec2(-1,1));
  gl_Position=vec4(v[gl_VertexIndex],(p.flags&8u)!=0u?0.7:0.3,1);color=vec4(0.1,0.1,0.1,1);return;}
 uint id=(p.mode==1u)?ids[gl_InstanceIndex]:uint(gl_InstanceIndex)+p.base;Object o=obj[id];
 uint lod=lods[id];uint subdivisions=1u<<(2u-min(lod,2u));uint tri=uint(gl_VertexIndex)/3u,corner=uint(gl_VertexIndex)%3u;
 vec2 a=vec2(-1,-1),b=vec2(1,-1),c=vec2(0,1);
 vec2 v=corner==0u?c:mix(a,b,float(tri+(corner==2u?1u:0u))/float(subdivisions));
 if(tri>=subdivisions)v=vec2(0); // Fixed particle instance topology: extra LOD triangles degenerate.
 gl_Position=vec4((o.sphere.x-p.viewX)*p.zoom+v.x*o.sphere.w*p.zoom,o.sphere.y*p.zoom+v.y*o.sphere.w*p.zoom,(p.flags&8u)!=0u?1-o.sphere.z:o.sphere.z,1);
 color=vec4(float((id*17u)%251u)/251.0,float((id*37u)%241u)/241.0,float((id*13u)%239u)/239.0,0.5);
}
