#version 450
layout(set=0,binding=0)uniform sampler2D emoji;
layout(location=0)in vec2 uv;
layout(location=0)out vec4 color;
layout(push_constant)uniform Params{vec4 unused;}pc;
void main(){color=texelFetch(emoji,ivec2(gl_FragCoord.xy),0)*.75;}
