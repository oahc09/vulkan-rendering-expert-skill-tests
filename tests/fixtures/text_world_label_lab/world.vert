#version 450
layout(location=0) in vec3 position;
layout(location=1) in vec2 atlasUV;
// INTERPOLATION
layout(location=0) out vec2 uv;
void main(){gl_Position=vec4(position.xy,(10.0/9.0)*position.z-10.0/9.0,position.z);uv=atlasUV;}
