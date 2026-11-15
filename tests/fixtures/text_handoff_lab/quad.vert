#version 450
layout(location=0) in vec2 xy;
layout(location=1) in vec2 uv;
layout(location=0) out vec2 vertexUV;
void main(){gl_Position=vec4(xy,0,1);vertexUV=uv;}
