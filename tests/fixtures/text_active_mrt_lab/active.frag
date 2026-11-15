#version 450
layout(set=0,binding=0) uniform sampler2D glyphCoverage;
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocityOut;
layout(location=2) out vec4 idOut;
layout(push_constant) uniform Params { vec4 linearTextColor; } params;
void main() {
    velocityOut=vec4(.9,.8,.7,.6);idOut=vec4(4,3,2,1);
    float coverage=texture(glyphCoverage,uv).r;
    float a=clamp(coverage,0.0,1.0)*params.linearTextColor.a;
    color=vec4(params.linearTextColor.rgb*a,a);
}
