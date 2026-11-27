#version 450
layout(location=0) in vec3 position;
layout(location=1) in vec3 faceColor;
layout(location=0) out vec3 tint;
void main(){vec2 p=position.xy+vec2(1,.5)*position.z;gl_Position=vec4(2*p/vec2(65,49)-1,.2+.05*position.z,1);tint=faceColor;}
