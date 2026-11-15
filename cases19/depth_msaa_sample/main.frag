#version 450
layout(push_constant) uniform Params { uint mode; } pc;
layout(location=0) out vec4 color;
void main(){ivec2 p=ivec2(gl_FragCoord.xy);if(pc.mode==0u){if(!(p.x<1+p.y%3))discard;gl_FragDepth=0.25;color=vec4(1,0,0,1);}else{gl_FragDepth=0.75;color=vec4(0,1,1,1);}}
