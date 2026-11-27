#version 450
layout(set=0,binding=0) uniform sampler2D glyphCoverage;
// INTERPOLATION
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 ids;
layout(push_constant) uniform Params {vec4 ink;} p;
void main(){if(p.ink.a<0){color=vec4(p.ink.rgb,1);}else{float c=texture(glyphCoverage,uv).r;float a=c*p.ink.a;color=vec4(p.ink.rgb*a,a);}velocity=vec4(9);ids=vec4(8);}
