// SPDX-License-Identifier: MIT
struct Particle { vec4 x; vec4 previous; }; // xyz + inverse mass, previous substep xyz
struct Edge { uint a; uint b; float rest; float compliance; };
layout(push_constant) uniform Push { uint n,capacity,mode,flags,width,height,level,tick; float viewX,zoom; uint base,unused; } p;
#ifdef READ_ONLY
#define RW readonly
#else
#define RW
#endif
layout(set=0,binding=0,std430) RW buffer InputState { Particle source[]; };
layout(set=0,binding=1,std430) RW buffer SolvedState { Particle state[]; };
layout(set=0,binding=2,std430) readonly buffer Edges { Edge edges[]; };
layout(set=0,binding=4,std430) RW buffer Lambdas { float lambda[]; };
layout(set=0,binding=5,std430) RW buffer Contributions { vec4 delta[]; };
layout(set=0,binding=7,std430) RW buffer Normals { vec4 normal[]; };
