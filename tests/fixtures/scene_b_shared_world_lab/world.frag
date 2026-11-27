#version 450
layout(location=0) in vec3 world;
layout(set=0,binding=0) uniform sampler2D sourceImage;
layout(push_constant) uniform Params {vec4 p;} pc;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 ids;
void main(){
 int kind=int(pc.p.z);color=vec4(.2,.6,.8,1);
 if(kind==0){ivec2 s=ivec2(floor(world.xy+vec2(.5,.25)*world.z));bool valid=all(greaterThanEqual(s,ivec2(0)))&&all(lessThan(s,ivec2(65,49)));bool dark=false;if(valid)dark=world.z/16>texelFetch(sourceImage,s,0).r;color=vec4(vec3(.8,.6,.4)*(dark&&pc.p.w==0?.25:1),1);}
 if(kind==2)color=vec4(.3,.25,.5,1);
 if(kind==3){ivec2 s=ivec2(floor(world.xy-vec2(32,15)));float a=texelFetch(sourceImage,s,0).r*.75;color=vec4(vec3(.9,.3,.1)*a,a);}
 velocity=vec4(8);ids=vec4(9);
}
