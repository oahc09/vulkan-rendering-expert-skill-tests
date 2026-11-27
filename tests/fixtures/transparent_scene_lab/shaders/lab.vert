#version 450
// Original synthetic orthographic, diagonal-covariance Gaussian reference.
struct Splat { vec4 center; vec4 shape; vec4 color; uvec4 identity; };
layout(set=0,binding=0,std430) readonly buffer Splats { Splat splats[]; };
layout(push_constant) uniform Push { uint n;uint capacity;uint mode;uint flags;uint width;uint height;uint level;uint tick;float viewX;float zoom;uint base;uint unused; } p;
layout(location=0) out vec2 q;
layout(location=1) flat out vec4 color;
layout(location=2) flat out uint mode;
layout(location=3) flat out uint gaussian;
layout(location=4) flat out uvec3 identity;
void main(){
 vec2 corners[6]=vec2[](vec2(-1,-1),vec2(1,-1),vec2(1,1),vec2(-1,-1),vec2(1,1),vec2(-1,1));
 Splat s=splats[p.base+gl_InstanceIndex];q=corners[gl_VertexIndex];
 // One-pixel conservative quad margin prevents raster subpixel snapping from
 // cutting nonzero Gaussian tails. Analytic ellipse discard retains the profile.
 if(s.identity.w!=0u) q*=1.0+vec2(2.0/float(p.width),2.0/float(p.height))/s.shape.xy;
 gl_Position=vec4(s.center.xy+vec2(p.viewX,0)+q*s.shape.xy,s.center.z,1);
 identity=s.identity.xyz;color=s.color;mode=p.mode;gaussian=s.identity.w;
}
