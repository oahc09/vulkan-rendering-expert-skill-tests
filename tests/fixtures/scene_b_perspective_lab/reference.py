import math
from fractions import Fraction
W,H=65,49

def inside(p,poly):
 x,y=p;n=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:n=not n
 return n

def ray_hits(poly,x,y,rx,ry,near):
 hits=[]
 for z in (0,6):
  if z+20>=near and inside((x+rx*z,y+ry*z),poly):hits.append((z,'cap'))
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ex=b[0]-a[0];ey=b[1]-a[1];den=rx*ey-ry*ex
  if not den:continue
  z=((a[0]-x)*ey-(a[1]-y)*ex)/den
  u=((x+rx*z-a[0])*ex+(y+ry*z-a[1])*ey)/(ex*ex+ey*ey)
  if 0<=z<=6 and z+20>=near and 0<=u<=1:hits.append((z,'side'))
 return min(hits) if hits else None

def frame(poly,g,shadow,offset,near,mirror):
 transformed=[(65-x if mirror else x,y) for x,y in poly]
 color=[];depth=[];roi=dict(cap=0,side=0,shadow=0,label_visible=0,label_hidden=0)
 for y in range(H):
  for x in range(W):
   rx=(x+.5-32.5)/40;ry=(y+.5-24.5)/40;ox=32.5+offset;oy=24.5
   qx=ox+20*rx;qy=oy+20*ry;wx=Fraction(65,2)+offset+(Fraction(2*x+1,2)-Fraction(65,2))*Fraction(30,40);wy=Fraction(49,2)+(Fraction(2*y+1,2)-Fraction(49,2))*Fraction(30,40);sx=math.floor(wx+5);sy=math.floor(wy+Fraction(5,2))
   dark=0<=sx<W and 0<=sy<H and .625>shadow[sy*W+sx]
   c=[v*(.25 if dark else 1) for v in (.8,.6,.4)]+[1];z=10;kind='shadow' if dark else None
   h=ray_hits(transformed,qx,qy,rx,ry,near)
   if h:z,kind=h;c=[.2,.6,.8,1]
   wx=Fraction(65,2)+offset+(Fraction(2*x+1,2)-Fraction(65,2))*Fraction(21,40);wy=Fraction(49,2)+(Fraction(2*y+1,2)-Fraction(49,2))*Fraction(21,40);sourcex=65-wx if mirror else wx
   if near<=21 and 34<=sourcex<43 and 17<=wy<28 and 1<z:z=1;kind=None;c=[.3,.25,.5,1]
   if kind:roi[kind]+=1
   wx=Fraction(65,2)+offset+(Fraction(2*x+1,2)-Fraction(65,2))*Fraction(23,40);wy=Fraction(49,2)+(Fraction(2*y+1,2)-Fraction(49,2))*Fraction(23,40);sourcex=65-wx if mirror else wx;gx=sourcex-32;gy=wy-15
   if near<=23 and 0<=gx<14 and 0<=gy<15:
    a=g[math.floor(gy)*14+math.floor(gx)]*.75
    if a:
     roi['label_visible' if 3<z else 'label_hidden']+=1
     if 3<z:c=[v*a+c[j]*(1-a) for j,v in enumerate((.9,.3,.1,1))]
   color.extend(c);depth.append(40/(40-near)*(1-near/(z+20)))
 return color,depth,roi

def boundary_centers():
 result={}
 for offset in (0,2):
  for mirror in (False,True):
   hits=[]
   for source in (34,43):
    wx=65-source if mirror else source
    screen=Fraction(65,2)+40*(Fraction(wx)-Fraction(65,2)-offset)/21
    if (screen-Fraction(1,2)).denominator==1:hits.append({'axis':'x','source':source,'pixel':int(screen-Fraction(1,2)),'included':source==34})
   for source in (17,28):
    screen=Fraction(49,2)+40*(Fraction(source)-Fraction(49,2))/21
    if (screen-Fraction(1,2)).denominator==1:hits.append({'axis':'y','source':source,'pixel':int(screen-Fraction(1,2)),'included':source==17})
   result[f'offset{offset}-mirror{int(mirror)}']=hits
 return result
