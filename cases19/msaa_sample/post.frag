#version 450
layout(set=0,binding=0) uniform sampler2D sourceImage;
layout(location=0) out vec4 color;
void main(){vec4 s=textureLod(sourceImage,gl_FragCoord.xy/vec2(4),0);color=s.brga;}
