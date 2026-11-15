// Fixed rectangular two-contour path and one round/butt segment, not general SVG.
bool vectorPanel(vec2 p,int mode){
 bool outer=p.x>=12&&p.x<44&&p.y>=8&&p.y<40;
 bool inner=p.x>=18&&p.x<36&&p.y>=15&&p.y<33;
 int iw=(mode==6||mode==7)?1:-1;
 int winding=(outer?1:0)+(inner?iw:0);
 bool ring=(mode==6||mode==8)?((int(outer)+int(inner))%2!=0):(winding!=0);
 if(mode==4)ring=outer;
 vec2 a=vec2(22,22),d=vec2(12,7),q=p-a;float dotd=dot(d,d),t=dot(q,d)/dotd;
 bool stroke=mode==5?(t>=0&&t<=1&&pow(q.x*d.y-q.y*d.x,2)<=4*dotd):dot(q-clamp(t,0,1)*d,q-clamp(t,0,1)*d)<=4;
 bool rect=p.x>=12&&p.x<43&&p.y>=10&&p.y<37;
 bool circle=dot(p-vec2(30,25),p-vec2(30,25))<=225;
 vec2 r0=p-vec2(18,8),r1=p-vec2(48,18),r2=p-vec2(40,42),r3=p-vec2(10,32);
 bool rotated=30*r0.y-10*r0.x>=0&&-8*r1.y-24*r1.x>=0&&-30*r2.y+10*r2.x>=0&&8*r3.y+24*r3.x>=0;
 return (ring||stroke)&&(rect||mode==1)&&(circle||mode==2)&&(rotated||mode==3);
}
