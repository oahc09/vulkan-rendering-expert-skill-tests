#version 450
layout(location=0) out vec4 color;
void main(){ivec2 p=ivec2(gl_FragCoord.xy);bool a=p.x < 1+(p.y%3);color=a?vec4(0,0,1,1):vec4(1,0,0,1);}
