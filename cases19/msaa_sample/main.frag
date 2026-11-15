#version 450
layout(location=0) out vec4 color;
void main(){ivec2 p=ivec2(gl_FragCoord.xy);color=vec4(p.x==0?1:0,p.y<2?1:0,p.x<1+p.y%3?1:0,1);}
