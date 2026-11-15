#version 450
layout(set=0,binding=0) uniform sampler2D glyphDistance;
layout(location=0) in vec2 vertexUV;
layout(location=0) out vec4 color;
layout(push_constant) uniform Params { vec4 linearTextColor; vec4 transform; } params;
float median3(vec3 v){return max(min(v.r,v.g),min(max(v.r,v.g),v.b));}
void main(){
 vec2 size=vec2(textureSize(glyphDistance,0));
 vec2 uv=((vertexUV*size-size*.5-vec2(params.transform.y,0))/params.transform.x+size*.5)/size;
 vec3 distance=texture(glyphDistance,uv).rgb;
#ifdef WRONG_SRGB
 distance=mix(distance/12.92,pow((distance+.055)/1.055,vec3(2.4)),greaterThan(distance,vec3(.04045)));
#endif
 float screenRange=max(.5*dot(vec2(params.transform.z)/size,vec2(1)/fwidth(uv)),1.);
#ifdef WRONG_CHANNEL
 float sd=distance.r;
#else
 float sd=median3(distance);
#endif
 float coverage=clamp((sd-.5)*screenRange+.5,0.,1.);
 float a=coverage*params.linearTextColor.a;
 color=vec4(params.linearTextColor.rgb*a,a);
}
