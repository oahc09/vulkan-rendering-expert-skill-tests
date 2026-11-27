"""CPU sampling and original per-glyph nonzero outline reference, not GPU outputs."""
import math
W,H=65,65
CENTER=(32.5,24.5)
BG=(.1,.2,.3,.5);INK=(.9,.5,.2)
def transform(x,y,t,inverse=False):
 if inverse:y-=8
 if t==5:t=2
 x-=32.5;y-=24.5
 if t==1:x=x/.75 if inverse else x*.75;y=y/.75 if inverse else y*.75
 elif t==2:x,y=(y,-x) if inverse else (-y,x)
 elif t in (3,4):x+=(-1 if inverse else 1)*(.25 if t==3 else .5)
 return x+32.5,y+24.5+(0 if inverse else 8)
def sample(layer,x,y,density=1):
 x*=density;y*=density
 x-=.5;y-=.5;ix=math.floor(x);iy=math.floor(y);fx=x-ix;fy=y-iy
 def at(xx,yy,c):return layer[4*(min(49*density-1,max(0,yy))*65*density+min(65*density-1,max(0,xx)))+c]
 return [sum(at(ix+dx,iy+dy,c)*(fx if dx else 1-fx)*(fy if dy else 1-fy) for dx in (0,1) for dy in (0,1)) for c in range(4)]
def expected(layers,t,mode,color=False):
 out=[];scale=.75 if t==1 else 1
 for y in range(H):
  for x in range(W):
   dst=list(BG)
   for layer in layers:
    if color:
     s=sample(layer,*transform(x+.5,y+.5,t,True));src=[v*.75 for v in s]
    else:
     if mode==0:cov=sample(layer,*transform(x+.5,y+.5,t,True))[0]
     else:
      cov=0
      for sy in range(4):
       for sx in range(4):
        rgb=sample(layer,*transform(x+(sx+.5)/4,y+(sy+.5)/4,t,True),density=4)[:3];sd=sorted(rgb)[1]-.5
        cov+=max(0,min(1,sd*4*scale*4+.5))/16
     alpha=cov*.75;src=[v*alpha for v in INK]+[alpha]
    dst=[src[c]+dst[c]*(1-src[3]) for c in range(4)]
   out.extend(dst)
 return out

def geometry(contours,t):
 edges=[]
 for contour in contours:
  for e in contour:
   n=1 if len(e)==2 else 64;last=e[0]
   for i in range(1,n+1):
    u=i/n;v=1-u;weights=(v,u) if len(e)==2 else ((v*v,2*v*u,u*u) if len(e)==3 else (v**3,3*v*v*u,3*v*u*u,u**3))
    nxt=tuple(sum(p[k]*a for p,a in zip(e,weights)) for k in (0,1));edges.append((transform(*last,t),transform(*nxt,t)));last=nxt
 out=[0.]*(W*H);N=16
 for y in range(H):
  for sy in range(N):
   yy=y+(sy+.5)/N;cross=[]
   for (ax,ay),(bx,by) in edges:
    if ay<=yy<by:cross.append((ax+(yy-ay)*(bx-ax)/(by-ay),1))
    elif by<=yy<ay:cross.append((ax+(yy-ay)*(bx-ax)/(by-ay),-1))
   cross.sort();winding=0;start=None
   for xx,change in cross:
    old=winding;winding+=change
    if old==0 and winding!=0:start=xx
    if old!=0 and winding==0:
     a=max(0,math.ceil(start*N-.5));b=min(W*N,math.ceil(xx*N-.5))
     for s in range(a,b):out[y*W+s//N]+=1/(N*N)
 return out

def outline_alpha(layers,t):
 alpha=[0.]*(W*H)
 for layer in layers:
  cov=geometry(layer['outline'],t)
  alpha=[c*.75+a*(1-c*.75) for a,c in zip(alpha,cov)]
 return alpha

def supported(row,t):
 if t==2 and not row.get('color'):return False,'historical rotate90 unsupported retained; new square-rotate90 is separate'
 for layer in row['layers']:
  if 'outline' not in layer:bounds=[(15,8),(49,40)]
  else:
   pts=[p for c in layer['outline'] for e in c for p in e]
   # Shared source margin includes distance range2 + bilinear1.
   if any(not(3<x<W-3 and 3<y<49-3) for x,y in pts):return False,'source distance padding'
   l,top,r,b=layer['bitmap_bounds'];bounds=pts+[(l-.5,top-.5),(r+.5,b+.5)]
  if any(not(0<=u<=W and 0<=v<=H) for u,v in [transform(x,y,t) for x,y in bounds]):return False,'transformed ink/sampling footprint outside tile'
 return True,None
