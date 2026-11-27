#version 450
layout(set=0,binding=0) uniform sampler2D atlas;
layout(location=0) out vec4 color;
layout(push_constant) uniform P{vec4 ink;vec4 info;vec4 extra;}p;
vec2 inv(vec2 q){if(int(p.info.x)==6){vec2 v=q-vec2(32.5);
#ifdef WRONG_INVERSE
 return v/.75+vec2(32.5,24.5);
#else
 float den=.75-v.x/128.;return vec2(v.x/den+32.5,v.y/den+24.5);
#endif
 }q.y-=8.;int t=int(p.info.x);q-=vec2(32.5,24.5);if(t==1)q/=.75;else if(t==2||t==5)q=vec2(q.y,-q.x);else if(t==3)q.x-=.25;else if(t==4)q.x-=.5;return q+vec2(32.5,24.5);}
vec4 sampleGlyph(vec2 q,int g){ivec4 a=ivec4(round(texelFetch(atlas,ivec2(3*g,0),0)*1024.));ivec4 b=ivec4(round(texelFetch(atlas,ivec2(3*g+1,0),0)*1024.));int density=b.z;
#ifdef WRONG_METADATA
 a.z+=density;
#endif
 q=q*float(density)-vec2(a.zw)-.5;ivec2 i=ivec2(floor(q));vec2 f=fract(q);if(density==1&&int(p.info.x)==1){ivec2 n=4*ivec2(floor(gl_FragCoord.xy))-ivec2(32,56);ivec2 whole=ivec2(floor(vec2(n)/3.));i=whole-a.zw;f=vec2(n-3*whole)/3.;}
#ifndef WRONG_INVERSE
 if(density==1&&int(p.info.x)==6){ivec2 pixel=ivec2(floor(gl_FragCoord.xy));int den=128-pixel.x;ivec2 n=ivec2(96*pixel.x,128*pixel.y-24*pixel.x-1024);ivec2 whole=ivec2(floor(vec2(n)/float(den)));i=whole-a.zw;f=vec2(n-den*whole)/float(den);}
#endif
 ivec2 lo=clamp(i,ivec2(0),b.xy-1)+a.xy,hi=clamp(i+1,ivec2(0),b.xy-1)+a.xy;
 return mix(mix(texelFetch(atlas,lo,0),texelFetch(atlas,ivec2(hi.x,lo.y),0),f.x),mix(texelFetch(atlas,ivec2(lo.x,hi.y),0),texelFetch(atlas,hi,0),f.x),f.y);}
float median3(vec3 a){return max(min(a.x,a.y),min(max(a.x,a.y),a.z));}
void main(){vec4 accum=vec4(0);float scale=int(p.info.x)==1?.75:1.;if(int(p.info.x)==6){vec2 v=gl_FragCoord.xy-vec2(32.5);float den=.75-v.x/128.;float jxx=.75/(den*den),jyx=v.y/(128.*den*den),jyy=1./den;scale=.5*(1./abs(jxx)+1./(abs(jyx)+abs(jyy)));}for(int g=0;g<int(p.info.z);g++){int mode=int(round(texelFetch(atlas,ivec2(3*g+1,0),0).w*1024.));vec4 src;if(mode==2)src=sampleGlyph(inv(gl_FragCoord.xy),g)*.75;else{float coverage=0.;if(mode==0)coverage=sampleGlyph(inv(gl_FragCoord.xy),g).r;else for(int y=0;y<4;y++)for(int x=0;x<4;x++){vec2 q=gl_FragCoord.xy+(vec2(x,y)+.5)/4.-.5;coverage+=clamp((median3(sampleGlyph(inv(q),g).rgb)-.5)*4.*scale*4.+.5,0.,1.)/16.;}float a=coverage*.75;src=vec4(p.ink.rgb*a,a);}accum=src+accum*(1.-src.a);}color=accum;}
