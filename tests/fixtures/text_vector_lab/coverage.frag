#version 450
layout(set=0,binding=0) uniform sampler2D glyphCoverage;
layout(location=0) in vec2 uv;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params { vec4 linearTextColor; } params;
void main() {
    float coverage=texture(glyphCoverage,uv).r;
    float a=clamp(coverage,0.0,1.0)*params.linearTextColor.a;
    color=vec4(params.linearTextColor.rgb*a,a);
}
