#version 450
layout(location=0) in vec2 uv;
layout(location=1) flat in uint material;
layout(location=0) out vec4 color;
void main(){if(material==1u && fract(uv.x*7.)>.5)discard;color=vec4(1);}
