#version 450
layout(set=0,binding=0) uniform sampler2D source;
layout(location=0) in vec2 vertexUV;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 id;
layout(push_constant) uniform Params {vec4 ink;} p;
void main(){float c=texture(source,vertexUV).r;color=vec4(p.ink.rgb*c,1);velocity=vec4(9);id=vec4(7);}
