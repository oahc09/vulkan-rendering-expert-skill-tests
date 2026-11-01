#ifdef VERTEX_READONLY
#define ACCESS readonly
#else
#define ACCESS
#endif
// SPDX-License-Identifier: MIT
struct Object { vec4 sphere; uvec4 meta; }; // 32-byte std430: xyz/r; id,residentMask,previousLOD,alive
struct Draw { uint vertexCount; uint instanceCount; uint firstVertex; uint firstInstance; };
layout(push_constant) uniform Push {
 uint n; uint capacity; uint mode; uint flags;
 uint width; uint height; uint level; uint tick;
 float viewX; float zoom; uint base; uint unused;
} p;
layout(set=0,binding=0,std430) readonly buffer Source { Object source[]; };
layout(set=0,binding=1,std430) ACCESS buffer Objects { Object obj[]; };
layout(set=0,binding=2,std430) ACCESS buffer Commands { Draw cmd[]; };
layout(set=0,binding=3,std430) ACCESS buffer Counters { uint count; uint overflow; uint written; uint padding; };
layout(set=0,binding=4,std430) ACCESS buffer Visible { uint ids[]; };
layout(set=0,binding=5,std430) ACCESS buffer Levels { float hiz[]; };
layout(set=0,binding=6) uniform sampler2D depthTex;
layout(set=0,binding=7,std430) ACCESS buffer Lods { uint lods[]; };
uint mipWidth(uint l) { return max(1u,(p.width+(1u<<l)-1u)>>l); }
uint mipHeight(uint l) { return max(1u,(p.height+(1u<<l)-1u)>>l); }
uint mipOffset(uint l) { uint o=0;for(uint i=0;i<l;i++)o+=mipWidth(i)*mipHeight(i);return o; }
