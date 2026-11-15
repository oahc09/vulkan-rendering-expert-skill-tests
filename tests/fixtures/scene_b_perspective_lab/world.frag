#version 450
#ifndef NEAR
#define NEAR 1
#endif
#ifndef MIRROR
#define MIRROR 0
#endif
layout(location=0)in vec3 world;
layout(set=0,binding=0)uniform sampler2D sourceImage;
layout(push_constant)uniform Params{vec4 p;}pc;
layout(location=0)out vec4 color;layout(location=1)out vec4 velocity;layout(location=2)out vec4 ids;
// PANEL
void main(){
 int kind=int(pc.p.z),ox=pc.p.x>0?0:2;ivec2 pixel=ivec2(gl_FragCoord.xy);color=vec4(.2,.6,.8,1);
 if(kind==0){ivec2 s=ivec2((54+4*ox+3*pixel.x)/4,(36+3*pixel.y)/4);bool valid=all(greaterThanEqual(s,ivec2(0)))&&all(lessThan(s,ivec2(65,49)));bool dark=false;if(valid)dark=.625>texelFetch(sourceImage,s,0).r;color=vec4(vec3(.8,.6,.4)*(dark&&pc.p.w==0?.25:1),1);}
 if(kind==2){ivec2 n=ivec2(MIRROR!=0?3944-42*pixel.x-80*ox:1256+42*pixel.x+80*ox,952+42*pixel.y);if(n.x<34*80||n.x>=43*80||n.y<17*80||n.y>=28*80)discard;color=vec4(.3,.25,.5,1);}
 if(kind==3){ivec2 n=ivec2(MIRROR!=0?1512-46*pixel.x-80*ox:46*pixel.x-1432+80*ox,46*pixel.y-344);if(any(lessThan(n,ivec2(0)))||n.x>=14*80||n.y>=15*80)discard;float a=texelFetch(sourceImage,n/80,0).r*.75;color=vec4(vec3(.9,.3,.1)*a,a);}
 if(kind==4){if(!vectorPanel(gl_FragCoord.xy,int(pc.p.w)))discard;color=vec4(vec3(.1,.85,.35)*.35,.35);}
 float vz=world.z+20;gl_FragDepth=kind==4?0:40.0/(40.0-float(NEAR))*((vz-float(NEAR))/vz);
 velocity=vec4(8);ids=vec4(9);
}
