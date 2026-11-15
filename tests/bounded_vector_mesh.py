"""Bounded simple-contour ear clipping; holes explicitly require mask fallback.
Uses the existing validated screen-space flattener, never a generic fan.
No stroke, extrusion, intersecting topology repair or general hole bridging.
"""
from bounded_vector_mask import flatten

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def triangulate(paths, *, transform=(1,0,0,1,0,0)):
    if len(paths)!=1:raise ValueError('holes/multiple contours require mask fallback')
    points=flatten(paths,transform=transform,max_segments=128)[0][:-1]
    n=len(points)
    area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))/2
    if abs(area)<1e-8:raise ValueError('degenerate area')
    sign=1 if area>0 else -1
    ids=list(range(n));triangles=[]
    while len(ids)>3:
        found=False
        for k,b in enumerate(ids):
            a,c=ids[k-1],ids[(k+1)%len(ids)]
            if sign*cross(points[a],points[b],points[c])<=1e-8:continue
            if any(all(sign*cross(points[u],points[v],points[p])>=-1e-8 for u,v in [(a,b),(b,c),(c,a)]) for p in ids if p not in (a,b,c)):continue
            triangles.append((a,b,c));del ids[k];found=True;break
        if not found:raise ValueError('unsafe ear topology; use mask fallback')
    if sign*cross(*(points[i] for i in ids))<=1e-8:raise ValueError('degenerate final triangle')
    triangles.append(tuple(ids))
    measured=sum(cross(*(points[i] for i in t))/2 for t in triangles)
    if len(triangles)!=n-2 or abs(measured-area)>1e-7*max(1,abs(area)):raise ValueError('area conservation')
    return points,triangles
