#version 450
layout(set=0,binding=0) uniform sampler2D glyphDistance;
layout(location=0) in vec2 vertexUV;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params { vec4 linearTextColor; vec4 transform; } params;
float median3(vec3 v){return max(min(v.r,v.g),min(max(v.r,v.g),v.b));}
void main(){
 vec2 size=vec2(textureSize(glyphDistance,0));
 vec2 uv=((vertexUV*size-size*.5-vec2(params.transform.y,0))/params.transform.x+size*.5)/size;
 vec2 dx=dFdx(uv),dy=dFdy(uv);
#ifdef LINEAR4
 const int N=4;
#else
 const int N=16;
#endif
 float coverage=0.;
 for(int y=0;y<N;y++)for(int x=0;x<N;x++){
  vec2 delta=(vec2(x,y)+.5)/float(N)-.5;
  vec3 d=texture(glyphDistance,uv+dx*delta.x+dy*delta.y).rgb;
#ifdef WRONG_SRGB
  d=mix(d/12.92,pow((d+.055)/1.055,vec3(2.4)),greaterThan(d,vec3(.04045)));
#endif
#ifdef LINEAR4
  coverage+=clamp((median3(d)-.5)*params.transform.z*params.transform.x*float(N)+.5,0.,1.)/float(N*N);
#else
  coverage+=step(.5,median3(d))/float(N*N);
#endif
 }
 float a=coverage*params.linearTextColor.a;
 color=vec4(params.linearTextColor.rgb*a,a);
}
