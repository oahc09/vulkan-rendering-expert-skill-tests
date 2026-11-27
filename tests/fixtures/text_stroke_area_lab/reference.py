"""Independent exact rational vertical-slice integration of a stroke rectangle."""
from fractions import Fraction as F

def polygon(case):
 # The registered directions are normalized rational pairs, not GPU vertices.
 a,b=case['points'];a=tuple(F(x) for x in a);b=tuple(F(x) for x in b);r=F(case['width'])/2
 dx,dy=b[0]-a[0],b[1]-a[1]
 if dy==0 and dx>0:u=(F(1),F(0))
 elif dx*3==dy*4 and dx>0:u=(F(4,5),F(3,5))
 else:raise ValueError('unsupported registered direction')
 if case['cap']=='square':a=(a[0]-r*u[0],a[1]-r*u[1]);b=(b[0]+r*u[0],b[1]+r*u[1])
 elif case['cap']!='butt':raise ValueError('unsupported cap')
 n=(-r*u[1],r*u[0]);return [(a[0]+n[0],a[1]+n[1]),(b[0]+n[0],b[1]+n[1]),(b[0]-n[0],b[1]-n[1]),(a[0]-n[0],a[1]-n[1])]

def area(case,x,y):
 # Break at polygon vertices and intersections with horizontal pixel bounds.
 # Each clipped vertical length is affine between these exact rational events.
 q=polygon(case);left,right=F(x),F(x+1);bottom,top=F(y),F(y+1);cuts={left,right}
 for a,b in zip(q,q[1:]+q[:1]):
  if left<a[0]<right:cuts.add(a[0])
  if a[1]!=b[1]:
   for h in (bottom,top):
    t=(h-a[1])/(b[1]-a[1])
    if 0<=t<=1:
     xx=a[0]+t*(b[0]-a[0])
     if left<xx<right:cuts.add(xx)
 def height(xx):
  ys=[]
  for a,b in zip(q,q[1:]+q[:1]):
   if a[0]!=b[0] and min(a[0],b[0])<=xx<=max(a[0],b[0]):ys.append(a[1]+(xx-a[0])*(b[1]-a[1])/(b[0]-a[0]))
  return max(F(0),min(top,max(ys))-max(bottom,min(ys))) if len(ys)>=2 else F(0)
 cuts=sorted(cuts);total=F(0)
 for a,b in zip(cuts,cuts[1:]):
  # Midpoint is exact for a linear function; avoids endpoint degeneracies.
  total+=(b-a)*height((a+b)/2)
 assert 0<=total<=1
 return total
