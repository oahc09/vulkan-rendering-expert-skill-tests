#version 450
layout(push_constant) uniform P{vec4 ink;vec4 info;vec4 extra;}p;
void main(){vec2 u[6]=vec2[](vec2(0,0),vec2(1,0),vec2(0,1),vec2(0,1),vec2(1,0),vec2(1,1));vec2 v=u[gl_VertexIndex];if(int(p.info.x)==6){vec2 q=v*vec2(65,49)-vec2(32.5,24.5);float w=1.+q.x/128.;gl_Position=vec4(2.*.75*q/65.,.5*w,w);}else gl_Position=vec4(2.*v-1.,.5,1.);}
