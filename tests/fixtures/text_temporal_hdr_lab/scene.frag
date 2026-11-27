#version 450
layout(binding=1,std430)readonly buffer Accum {vec4 accumulated[];};
layout(push_constant)uniform Params{vec4 mode;}p;
layout(location=0)out vec4 color;
layout(location=1)out vec4 velocity;
layout(location=2)out vec4 id;
void main(){uint i=uint(gl_FragCoord.y)*65+uint(gl_FragCoord.x);vec3 rgb=vec3(4,2,1)*(.25+.75*accumulated[i].x);if(p.mode.x>0)rgb=rgb/(1+rgb);color=vec4(rgb,1);velocity=vec4(9);id=vec4(9);}
