"""Bounded screen-space CPU path->coverage fallback, not a tessellator/SVG engine.
Supports closed M/L/Q/C/Z contours, affine transforms, nonzero/evenodd fills.
Rejects touching/self-crossing contours, singular transforms and budget overflow.
No strokes, perspective, nested clips, extrusion, boolean topology or font parser.
"""
import math

def flatten(paths, *, transform=(1,0,0,1,0,0), tolerance=.125, max_segments=512, max_depth=16):
    if not 0<tolerance<=1 or not math.isfinite(tolerance):raise ValueError('tolerance')
    if type(max_segments)!=int or not 3<=max_segments<=4096:raise ValueError('segment budget')
    if type(max_depth)!=int or not 1<=max_depth<=20:raise ValueError('depth budget')
    if len(transform)!=6 or not all(math.isfinite(x) for x in transform):raise ValueError('transform')
    a,b,c,d,e,f=transform
    if abs(a*d-b*c)<1e-10:raise ValueError('singular affine transform')
    if not paths or len(paths)>32:raise ValueError('contour budget')
    count=0
    def point(x,y):
        if not all(math.isfinite(v) and abs(v)<=1e6 for v in (x,y)):raise ValueError('coordinate')
        p=(a*x+c*y+e,b*x+d*y+f)
        if not all(math.isfinite(v) and abs(v)<=1e6 for v in p):raise ValueError('transformed coordinate')
        return p
    def emit(out,p):
        nonlocal count
        if p==out[-1]:raise ValueError('zero length/repeated edge')
        count+=1
        if count>max_segments:raise ValueError('segment budget exceeded')
        out.append(p)
    def flat(points):
        p,q=points[0],points[-1];dx=q[0]-p[0];dy=q[1]-p[1];den=dx*dx+dy*dy
        if not den:return False
        # Distance to the finite chord; unlike line distance, catches collinear
        # curves whose controls overshoot/backtrack beyond an endpoint.
        return all(math.hypot(v[0]-(p[0]+max(0,min(1,((v[0]-p[0])*dx+(v[1]-p[1])*dy)/den))*dx),
                              v[1]-(p[1]+max(0,min(1,((v[0]-p[0])*dx+(v[1]-p[1])*dy)/den))*dy))<=tolerance for v in points[1:-1])
    def curve(out,pts,depth):
        if flat(pts):emit(out,pts[-1]);return
        if depth>=max_depth:raise ValueError('subdivision depth exceeded')
        levels=[pts]
        while len(levels[-1])>1:
            prev=levels[-1];levels.append([((x[0]+y[0])/2,(x[1]+y[1])/2) for x,y in zip(prev,prev[1:])])
        curve(out,[row[0] for row in levels],depth+1)
        curve(out,[row[-1] for row in reversed(levels)],depth+1)
    result=[]
    for commands in paths:
        if not commands or len(commands)>max_segments+1:raise ValueError('command budget')
        out=[];closed=False
        for cmd in commands:
            if not cmd or closed:raise ValueError('command after close')
            op,*v=cmd
            n={'M':2,'L':2,'Q':4,'C':6,'Z':0}.get(op)
            if n is None or len(v)!=n:raise ValueError('unsupported command')
            if op=='M':
                if out:raise ValueError('nested move')
                out=[point(*v)];continue
            if not out:raise ValueError('missing move')
            if op=='L':emit(out,point(*v))
            elif op in ('Q','C'):curve(out,[out[-1]]+[point(*v[i:i+2]) for i in range(0,n,2)],0)
            else:
                if out[-1]!=out[0]:emit(out,out[0])
                closed=True
        if not closed or len(out)<4:raise ValueError('unclosed/degenerate contour')
        result.append(out)
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    edges=[(ci,i,a,b) for ci,p in enumerate(result) for i,(a,b) in enumerate(zip(p,p[1:]))]
    for idx,(ci,i,a,b) in enumerate(edges):
        for cj,j,c,d in edges[idx+1:]:
            if ci==cj and (abs(i-j)==1 or {i,j}=={0,len(result[ci])-2}):continue
            if max(a[0],b[0])<min(c[0],d[0]) or max(c[0],d[0])<min(a[0],b[0]) or max(a[1],b[1])<min(c[1],d[1]) or max(c[1],d[1])<min(a[1],b[1]):continue
            if orient(a,b,c)*orient(a,b,d)<=0 and orient(c,d,a)*orient(c,d,b)<=0:raise ValueError('unsupported intersecting/touching topology')
    for p in result:
        vertices=p[:-1]
        for i,v in enumerate(vertices):
            before=vertices[i-1];after=vertices[(i+1)%len(vertices)]
            if abs(orient(before,v,after))<1e-12 and (v[0]-before[0])*(after[0]-v[0])+(v[1]-before[1])*(after[1]-v[1])<=0:
                raise ValueError('adjacent backtracking topology')
        if abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:])))<1e-9:raise ValueError('zero area')
    return result

def coverage(paths,width,height,*,fill='nonzero',samples=4,max_work=8_000_000,**kwargs):
    if fill not in ('nonzero','evenodd'):raise ValueError('fill')
    if type(width)!=int or type(height)!=int or not 0<width*height<=65536 or min(width,height)<=0:raise ValueError('mask budget')
    if type(samples)!=int or not 1<=samples<=8:raise ValueError('sample budget')
    if type(max_work)!=int or max_work<=0:raise ValueError('work budget')
    polygons=flatten(paths,**kwargs)
    edges=[(a,b) for p in polygons for a,b in zip(p,p[1:])]
    if width*height*samples*samples*len(edges)>min(max_work,8_000_000):raise ValueError('work budget')
    def inside(x,y):
        winding=0
        for a,b in edges:
            cross=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
            if a[1]<=y<b[1] and cross>0:winding+=1
            elif b[1]<=y<a[1] and cross<0:winding-=1
        return winding!=0 if fill=='nonzero' else winding%2!=0
    return [sum(inside(x+(sx+.5)/samples,y+(sy+.5)/samples) for sy in range(samples) for sx in range(samples))/(samples*samples) for y in range(height) for x in range(width)]
