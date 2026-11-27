#version 450
layout(location=0) in vec3 tint;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 ids;
void main(){color=vec4(tint,1);velocity=vec4(9);ids=vec4(8);}
