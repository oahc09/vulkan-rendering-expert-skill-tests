#version 450
layout(set=0,binding=0) uniform sampler2D layers;
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params {vec4 back;vec4 front;} params;
void main(){vec2 m=texture(layers,uv).rg;float a=m.r*params.back.a,b=m.g*params.front.a;vec4 first=vec4(params.back.rgb*a,a);color=vec4(params.front.rgb*b,b)+first*(1.-b);}
