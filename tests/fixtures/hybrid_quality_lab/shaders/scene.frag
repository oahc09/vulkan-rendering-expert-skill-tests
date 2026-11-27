#version 450
layout(location=0) in vec2 uv;
layout(location=1) flat in uint material;
layout(location=0) out vec4 color;
#ifdef GRID_STABLE
layout(location=2) flat in ivec2 cutoutColumns;
void main(){
 if(material==1u){
   int x=int(gl_FragCoord.x)-cutoutColumns.x;
   int width=cutoutColumns.y-cutoutColumns.x;
   // Test the texel center against a rational 7-bar pattern with a tie-inclusive opaque half.
   int phase=((2*x+1)*7) % (2*width);
   if(phase>width) discard;
 }
 color=vec4(1);
}
#else
void main(){if(material==1u && fract(uv.x*7.)>.5)discard;color=vec4(1);}
#endif
