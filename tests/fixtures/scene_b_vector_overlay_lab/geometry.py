"""Frozen hard pixel-center vector/clip reference, independent of GPU source."""
import math
OUTER=((12,8),(44,8),(44,40),(12,40));INNER=((18,15),(18,33),(36,33),(36,15))
ROTATED=((18,8),(48,18),(40,42),(10,32));START=(22,22);END=(34,29);RADIUS=2

def winding(p,poly):
 n=0;x,y=p
 for a,b in zip(poly,poly[1:]+poly[:1]):
  c=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
  if a[1]<=y<b[1] and c>0:n+=1
  if b[1]<=y<a[1] and c<0:n-=1
 return n

def closed_polygon(p,poly):
 for a,b in zip(poly,poly[1:]+poly[:1]):
  dx=b[0]-a[0];dy=b[1]-a[1];qx=p[0]-a[0];qy=p[1]-a[1]
  if dx*qy-dy*qx==0 and 0<=qx*dx+qy*dy<=dx*dx+dy*dy:return True
 return winding(p,poly)!=0

def layers(p):
 x,y=p
 return (12<=x<43 and 10<=y<37,math.hypot(x-30,y-25)<=15,closed_polygon(p,ROTATED))

def source(p,mode=0):
 x,y=p;w=winding(p,OUTER)+winding(p,INNER)
 outer=winding(p,OUTER);inner=winding(p,INNER)
 if mode in (6,7):inner=-inner
 ring=((abs(outer)+abs(inner))%2!=0) if mode in (6,8) else (outer+inner)!=0
 if mode==4:ring=outer!=0
 dx=END[0]-START[0];dy=END[1]-START[1];t=((x-START[0])*dx+(y-START[1])*dy)/(dx*dx+dy*dy)
 if mode==5:stroke=0<=t<=1 and abs((x-START[0])*dy-(y-START[1])*dx)<=RADIUS*math.hypot(dx,dy)
 else:
  t=max(0,min(1,t));stroke=math.hypot(x-START[0]-t*dx,y-START[1]-t*dy)<=RADIUS
 return ring,stroke

def covered(p,mode=0):
 r,s=source(p,mode);clip=layers(p)
 return (r or s) and all(v or mode==i+1 for i,v in enumerate(clip))

def overlay(colors,mode=0):
 out=list(colors)
 for y in range(49):
  for x in range(65):
   if covered((x+.5,y+.5),mode):
    i=(y*65+x)*4;out[i:i+4]=[v*.35+out[i+j]*.65 for j,v in enumerate((.1,.85,.35,1))]
 return out

def preflight():
 points=[(x+.5,y+.5) for y in range(49) for x in range(65)]
 counts={f'negative_{m}':sum(covered(p)!=covered(p,m) for p in points) for m in range(1,6)}
 counts['path_only']=sum(source(p)==(True,False) and covered(p) for p in points)
 counts['stroke_only']=sum(source(p)==(False,True) and covered(p) for p in points)
 counts['hole_kept']=sum(winding(p,INNER)!=0 and not covered(p) and all(layers(p)) for p in points)
 return counts
