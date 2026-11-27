"""Closed analytic screen-space stroke reference from original paths, never mesh."""
import math

def covered(c,x,y):
 p=c['points'];r=c['width']/2;yes=False
 for i,(a,b) in enumerate(zip(p,p[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];l2=dx*dx+dy*dy;px,py=x-a[0],y-a[1];dot=px*dx+py*dy;cross=px*dy-py*dx
  lo=-r*math.sqrt(l2) if c['cap']=='square' and i==0 else 0
  hi=l2+r*math.sqrt(l2) if c['cap']=='square' and i==len(p)-2 else l2
  yes |= lo<=dot<=hi and cross*cross<=r*r*l2
 if c['cap']=='round':
  yes |= any((x-a[0])**2+(y-a[1])**2<=r*r for a in (p[0],p[-1]))
 if len(p)==3:
  a,b,d=p;u=((b[0]-a[0])/math.dist(a,b),(b[1]-a[1])/math.dist(a,b));v=((d[0]-b[0])/math.dist(b,d),(d[1]-b[1])/math.dist(b,d));turn=u[0]*v[1]-u[1]*v[0];dot=u[0]*v[0]+u[1]*v[1]
  if abs(turn)>1e-8:
   sign=1 if turn>0 else -1;n1=(sign*u[1],-sign*u[0]);n2=(sign*v[1],-sign*v[0]);q1=(b[0]+r*n1[0],b[1]+r*n1[1]);q2=(b[0]+r*n2[0],b[1]+r*n2[1]);ratio=math.sqrt(2/(1+dot));tip=(b[0]+r*(n1[0]+n2[0])/(1+dot),b[1]+r*(n1[1]+n2[1])/(1+dot));poly=[b,q1,tip,q2] if c['join']=='miter' and ratio<=c['miter_limit'] else [b,q1,q2]
   # Convex polygon oriented halfplanes; no GPU triangulation or GLSL intersection.
   s=[(v[0]-u[0])*(y-u[1])-(v[1]-u[1])*(x-u[0]) for u,v in zip(poly,poly[1:]+poly[:1])]
   yes |= all(k>=0 for k in s) or all(k<=0 for k in s)
 return yes
