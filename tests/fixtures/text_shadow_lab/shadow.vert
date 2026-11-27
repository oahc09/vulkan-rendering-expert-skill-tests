#version 450
layout(location=0)in vec3 p;
void main(){gl_Position=vec4(2*(p.xy+vec2(.5,.25)*p.z)/vec2(65,49)-1,p.z/16,1);}
