#version 450
layout(set=0,binding=0) uniform sampler2D glyphCoverage;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params {vec4 linearTextColor;vec4 transform;} params;
void main(){float c=texelFetch(glyphCoverage,ivec2(gl_FragCoord.xy),0).r;float a=c*params.linearTextColor.a;color=vec4(params.linearTextColor.rgb*a,a);}
