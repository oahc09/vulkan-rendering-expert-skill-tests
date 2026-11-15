#version 450
layout(location=0) in vec3 position;
layout(location=1) in vec2 atlasUV;
layout(location=0) out vec2 uv;
layout(push_constant) uniform Params {vec4 ink;mat4 view;} p;
void main(){vec4 v=p.view*vec4(position,1);gl_Position=vec4(v.xy,(10.0/9.0)*v.z-10.0/9.0,v.z);uv=atlasUV;}
