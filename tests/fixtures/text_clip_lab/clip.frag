#version 450
#ifndef BYPASS_CLIP
#define BYPASS_CLIP 0
#endif
layout(set=0,binding=0) uniform sampler2D glyphCoverage;
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params { vec4 linearTextColor; } params;
float cross2(vec2 a,vec2 b){return a.x*b.y-a.y*b.x;}
void main(){
 vec2 p=gl_FragCoord.xy;
 bool outer=p.x>=12.0&&p.x<43.0&&p.y>=10.0&&p.y<37.0;
 bool circle=dot(p-vec2(30,25),p-vec2(30,25))<=225.0;
 bool rotated=cross2(vec2(30,10),p-vec2(18,8))>=0.0
  &&cross2(vec2(-8,24),p-vec2(48,18))>=0.0
  &&cross2(vec2(-30,-10),p-vec2(40,42))>=0.0
  &&cross2(vec2(8,-24),p-vec2(10,32))>=0.0;
 if((BYPASS_CLIP!=1&&!outer)||(BYPASS_CLIP!=2&&!circle)||(BYPASS_CLIP!=3&&!rotated))discard;
 float a=clamp(texture(glyphCoverage,uv).r,0,1)*params.linearTextColor.a;
 color=vec4(params.linearTextColor.rgb*a,a);
}
