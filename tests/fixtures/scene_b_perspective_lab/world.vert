#version 450
#ifndef MIRROR
#define MIRROR 0
#endif
#ifndef NEAR
#define NEAR 1
#endif
layout(location=0)in vec3 position;
layout(location=0)out vec3 world;
layout(push_constant)uniform Params{vec4 p;}pc;
void main(){
 if(pc.p.z==4){world=position;gl_Position=vec4(position.xy/vec2(65,49)*2-1,0,1);return;}
 world=vec3(MIRROR!=0?65-position.x:position.x,position.yz);
 float w=world.z+20,offsetX=pc.p.x>0?0:2;
 vec2 q=world.xy-vec2(32.5+offsetX,24.5);
 gl_Position=vec4(80*q/vec2(65,49),40.0/(40.0-float(NEAR))*(w-float(NEAR)),w);
}
