#version 450
layout(location=0) in vec2 q;
layout(location=1) flat in vec4 color;
layout(location=2) flat in uint mode;
layout(location=3) flat in uint gaussian;
layout(location=0) out vec4 result;
layout(location=4) flat in uvec3 identity;
void main(){
 float r2=dot(q,q);if(gaussian!=0u && r2>1.0) discard;
 float a=color.a*(gaussian!=0u?exp(-4.5*r2):1.0);
 // WBOIT constant weight=1: accumulation and revealage are separate raster passes.
 result=mode==1u?vec4(color.rgb*a,a):mode==2u?vec4(a):color;
 if(mode==3u){if(a<0.01)discard;result=vec4(vec3(identity),gl_FragCoord.z);}
 if(mode==0u) result.a=a; // straight source; pipeline multiplies RGB exactly once
}
