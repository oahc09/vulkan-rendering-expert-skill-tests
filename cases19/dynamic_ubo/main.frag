#version 450
layout(set=0,binding=0,std140) uniform Parameters {uvec4 rgba;} p[2];
layout(location=0) out vec4 color;
void main(){ivec2 pixel=ivec2(gl_FragCoord.xy);uvec4 a=p[0].rgba;uvec4 b=p[1].rgba;color=vec4(pixel.x < 1+(pixel.y%3)?a:b)/255.0;}
