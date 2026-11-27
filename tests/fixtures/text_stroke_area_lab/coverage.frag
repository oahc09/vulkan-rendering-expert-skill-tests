#version 450
layout(location=0) in vec3 tint;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 ids;
// CONSTANTS
vec2 tmp[12];vec2 poly[12];
int clipPoly(int n,int axis,float bound,bool lower){
 int m=0;vec2 a=poly[n-1];bool ain=lower?a[axis]>=bound:a[axis]<=bound;
 for(int i=0;i<n;i++){
  vec2 b=poly[i];bool bin=lower?b[axis]>=bound:b[axis]<=bound;
  if(ain!=bin){int other=1-axis;vec2 q;q[axis]=bound;q[other]=(a[other]*b[axis]-b[other]*a[axis]+bound*(b[other]-a[other]))/(b[axis]-a[axis]);tmp[m++]=q;}
  if(bin)tmp[m++]=b;a=b;ain=bin;
 }
 for(int i=0;i<m;i++)poly[i]=tmp[i];return m;
}
float pixelArea(){
 for(int i=0;i<4;i++)poly[i]=CORNERS[i]-gl_FragCoord.xy;
 int n=4;
 for(int axis=0;axis<2;axis++){
  n=clipPoly(n,axis,-.5,true);if(n==0)return 0;
  n=clipPoly(n,axis,.5,false);if(n==0)return 0;
 }
 float sum=0;
 for(int i=0;i<n;i++){vec2 a=poly[i],b=poly[(i+1)%n];sum+=a.x*b.y-a.y*b.x;}
 return clamp(abs(sum)*.5,0,1);
}
bool center(){
 float sign=0;bool pos=true,neg=true;
 for(int i=0;i<4;i++){vec2 a=CORNERS[i],b=CORNERS[(i+1)%4];float v=(b.x-a.x)*(gl_FragCoord.y-a.y)-(b.y-a.y)*(gl_FragCoord.x-a.x);pos=pos&&v>=0;neg=neg&&v<=0;}
 return pos||neg;
}
void main(){float c=HARD?(center()?1:0):pixelArea();if(c<=0)discard;float a=c*.75;color=vec4(tint*a*(DOUBLE_ALPHA?a:1),a);velocity=vec4(9);ids=vec4(8);}
