"""Finite screen-pixel polyline stroke mesh; no curves/dashes/SVG support."""
import math
CAP_STEPS=64

def generate(points,width,cap='butt',join='bevel',miter_limit=2.,*,dash=None,path_kind='polyline',max_triangles=256):
 if path_kind!='polyline' or dash is not None:raise ValueError('unsupported curve/dash')
 if cap not in ('butt','square','round') or join not in ('bevel','miter'):raise ValueError('unsupported cap/join')
 def valid(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
 if not valid(width) or not 0<width<=8:raise ValueError('width budget')
 if not valid(miter_limit) or not 1<=miter_limit<=8:raise ValueError('miter limit')
 if not isinstance(points,(list,tuple)) or len(points) not in (2,3):raise ValueError('polyline size')
 if any(not isinstance(p,(list,tuple)) or len(p)!=2 or any(not valid(x) for x in p) for p in points):raise ValueError('finite points')
 if type(max_triangles)!=int or not 1<=max_triangles<=256:raise ValueError('triangle budget')
 p=[tuple(map(float,x)) for x in points];r=width/2;dirs=[]
 for a,b in zip(p,p[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
  if length<=1e-8:raise ValueError('zero segment')
  dirs.append((dx/length,dy/length))
 join_data=None
 if len(dirs)==2:
  u,v=dirs;cross=u[0]*v[1]-u[1]*v[0];dot=u[0]*v[0]+u[1]*v[1]
  if dot<=-1+1e-8:raise ValueError('reversal unsupported')
  if abs(cross)>1e-8:
   sign=1 if cross>0 else -1;n1=(sign*u[1],-sign*u[0]);n2=(sign*v[1],-sign*v[0]);b=p[1]
   a=(b[0]+r*n1[0],b[1]+r*n1[1]);c=(b[0]+r*n2[0],b[1]+r*n2[1])
   # Intersection of the two offset lines, independent of oracle bisector formula.
   tx,ty=c[0]-a[0],c[1]-a[1];t=(tx*v[1]-ty*v[0])/cross;tip=(a[0]+t*u[0],a[1]+t*u[1]);ratio=math.hypot(tip[0]-b[0],tip[1]-b[1])/r
   effective='miter' if join=='miter' and ratio<=miter_limit else 'bevel';join_data=(b,a,c,tip,effective,ratio)
 required=2*len(dirs)+(4 if cap=='square' else 2*CAP_STEPS if cap=='round' else 0)+(0 if join_data is None else 2 if join_data[4]=='miter' else 1)
 if required>max_triangles:raise ValueError('triangle budget')
 triangles=[]
 def poly(q):
  for i in range(1,len(q)-1):triangles.append((q[0],q[i],q[i+1]))
 for a,b,u in zip(p,p[1:],dirs):
  n=(-u[1]*r,u[0]*r);poly([(a[0]+n[0],a[1]+n[1]),(b[0]+n[0],b[1]+n[1]),(b[0]-n[0],b[1]-n[1]),(a[0]-n[0],a[1]-n[1])])
 for center,u,sign in [(p[0],dirs[0],-1),(p[-1],dirs[-1],1)]:
  if cap=='round':
   for i in range(CAP_STEPS):
    a=2*math.pi*i/CAP_STEPS;b=2*math.pi*(i+1)/CAP_STEPS;triangles.append((center,(center[0]+r*math.cos(a),center[1]+r*math.sin(a)),(center[0]+r*math.cos(b),center[1]+r*math.sin(b))))
  elif cap=='square':
   n=(-u[1]*r,u[0]*r);tip=(center[0]+sign*r*u[0],center[1]+sign*r*u[1]);poly([(center[0]+n[0],center[1]+n[1]),(tip[0]+n[0],tip[1]+n[1]),(tip[0]-n[0],tip[1]-n[1]),(center[0]-n[0],center[1]-n[1])])
 if join_data:
  b,a,c,tip,effective,ratio=join_data;triangles.append((b,a,c))
  if effective=='miter':triangles.append((a,tip,c))
 if len(triangles)!=required or any(not(0<=x<=65 and 0<=y<=49) for tri in triangles for x,y in tri):raise ValueError('output bounds')
 return triangles,{'triangles':required,'effective_join':join_data[4] if join_data else 'none','miter_ratio':join_data[5] if join_data else None}
