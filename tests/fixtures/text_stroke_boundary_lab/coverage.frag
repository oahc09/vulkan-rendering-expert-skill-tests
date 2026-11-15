#version 450
layout(location=0) in vec3 tint;
layout(location=0) out vec4 color;
layout(location=1) out vec4 velocity;
layout(location=2) out vec4 ids;
// CASE_CONSTANTS
float cross2(vec2 a,vec2 b){return a.x*b.y-a.y*b.x;}
bool tri(vec2 p,vec2 a,vec2 b,vec2 c){float x=cross2(b-a,p-a),y=cross2(c-b,p-b),z=cross2(a-c,p-c);return (x>=0&&y>=0&&z>=0)||(x<=0&&y<=0&&z<=0);}
bool stroke(vec2 p){
 bool hit=false;float r=WIDTH*.5;
 for(int i=0;i<COUNT-1;i++){
  vec2 a=POINTS[i],b=POINTS[i+1],d=b-a,q=p-a;float l2=dot(d,d),t=dot(q,d),s=cross2(q,d);
  float low=(CAP==1&&i==0)?-r*sqrt(l2):0;
  float high=l2+((CAP==1&&i==COUNT-2)?r*sqrt(l2):0);
  bool terminal=OPEN_END&&i==COUNT-2 ? t<high : t<=high;
  hit=hit||(t>=low&&terminal&&s*s<=r*r*l2);
 }
 if(CAP==2){vec2 a=p-POINTS[0],b=p-POINTS[COUNT-1];hit=hit||dot(a,a)<=r*r||dot(b,b)<=r*r;}
 if(COUNT==3){
  vec2 b=POINTS[1],u=normalize(b-POINTS[0]),v=normalize(POINTS[2]-b);float turn=cross2(u,v);
  if(abs(turn)>1e-8){float sign=turn>0?1:-1;vec2 n1=sign*vec2(u.y,-u.x),n2=sign*vec2(v.y,-v.x);vec2 a=b+r*n1,c=b+r*n2;
   // Offset-line intersection rather than CPU angle-bisector polygon formula.
   vec2 tip=a+u*cross2(c-a,v)/turn;float ratio=length(tip-b)/r;
   hit=hit||tri(p,b,a,c);if(MITER&&ratio<=LIMIT)hit=hit||tri(p,a,tip,c);
  }
 }
 return hit;
}
void main(){if(!stroke(gl_FragCoord.xy))discard;color=vec4(tint,1);velocity=vec4(9);ids=vec4(8);}
