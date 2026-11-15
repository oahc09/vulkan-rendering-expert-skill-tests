#version 450
layout(set=0,binding=0) uniform sampler2D bands;
layout(location=0) out vec4 color;
layout(push_constant) uniform P {vec4 ink;vec4 info;} p;
vec2 inv(vec2 q){q-=vec2(32.5,24.5);int t=int(p.info.x);if(t==1)q/=.75;else if(t==2)q=vec2(q.y,-q.x);else if(t==3)q.x-=.25;else if(t==4)q.x-=.5;return q+vec2(32.5,24.5);}
vec4 sampleBand(vec2 q,int layer){q-=.5;ivec2 i=ivec2(floor(q));vec2 f=fract(q);ivec2 a=clamp(i,ivec2(0),ivec2(64,48)),b=clamp(i+1,ivec2(0),ivec2(64,48));a.y+=49*layer;b.y+=49*layer;return mix(mix(texelFetch(bands,a,0),texelFetch(bands,ivec2(b.x,a.y),0),f.x),mix(texelFetch(bands,ivec2(a.x,b.y),0),texelFetch(bands,b,0),f.x),f.y);}
// Fixed scale 3/4: derive texel-space index/remainder without center subtraction
// cancellation. Negative numerators use explicit mathematical floor division.
vec4 bitmapSample(vec2 pixel,int layer){
 if(int(p.info.x)!=1)return sampleBand(inv(pixel),layer);
 ivec2 n=4*ivec2(floor(pixel))-ivec2(32,24);
 ivec2 i=ivec2(floor(vec2(n)/3.));ivec2 rem=n-3*i;
 vec2 f=vec2(rem)/3.;ivec2 a=clamp(i,ivec2(0),ivec2(64,48)),b=clamp(i+1,ivec2(0),ivec2(64,48));a.y+=49*layer;b.y+=49*layer;
 return mix(mix(texelFetch(bands,a,0),texelFetch(bands,ivec2(b.x,a.y),0),f.x),mix(texelFetch(bands,ivec2(a.x,b.y),0),texelFetch(bands,b,0),f.x),f.y);
}
float med(vec3 v){return max(min(v.x,v.y),min(max(v.x,v.y),v.z));}
void main(){vec4 accum=vec4(0);float scale=int(p.info.x)==1?.75:1.;for(int g=0;g<int(p.info.z);g++){
 vec4 src;
 if(p.info.w>0){src=bitmapSample(gl_FragCoord.xy,g)*p.ink.a;}
 else{float cov=0.;if(p.info.y<.5)cov=bitmapSample(gl_FragCoord.xy,g).r;else{
 float range=4.;
#ifdef WRONG_RANGE
 range=1.;
#endif
 for(int y=0;y<4;y++)for(int x=0;x<4;x++){vec2 q=gl_FragCoord.xy+(vec2(x,y)+.5)/4.-.5;cov+=clamp((med(sampleBand(inv(q),g).rgb)-.5)*range*scale*4.+.5,0.,1.)/16.;}}
 float a=cov*p.ink.a;
#ifdef DOUBLE_ALPHA
 a*=cov;
#endif
 src=vec4(p.ink.rgb*a,a);}
 accum=src+accum*(1.-src.a);
 }color=accum;}
