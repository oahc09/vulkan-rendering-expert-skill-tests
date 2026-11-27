#version 450
layout(location=0) in vec3 position;
layout(location=0) out vec3 world;
layout(push_constant) uniform Params {vec4 p;} pc;
void main(){world=position;vec2 q=position.xy+pc.p.xy*position.z;gl_Position=vec4(q/vec2(65,49)*2-1,position.z/16,1);}
