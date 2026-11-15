#version 450
layout(set=0,binding=0)uniform sampler2D shadowDepth;
layout(push_constant)uniform Params{vec4 mode;} pc;
layout(location=0)out vec4 color;
layout(location=1)out vec4 velocity;
layout(location=2)out vec4 id;
void main(){ivec2 q=ivec2(floor(gl_FragCoord.xy+vec2(5,2.5)));bool inside=all(greaterThanEqual(q,ivec2(0)))&&all(lessThan(q,ivec2(65,49)));bool blocked=false;if(inside)blocked=.625>texelFetch(shadowDepth,q,0).r;float light=(blocked&&pc.mode.x==0)? .25:1;color=vec4(vec3(.8,.6,.4)*light,1);velocity=vec4(9);id=vec4(9);}
