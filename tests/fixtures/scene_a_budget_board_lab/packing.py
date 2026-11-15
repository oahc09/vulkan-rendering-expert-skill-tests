import math
W,H=65,49

def crop(layer,color=False):
 if color:return (14,7,50,41)
 pts=[p for c in layer['outline'] for e in c for p in e]
 return (max(0,math.floor(min(p[0] for p in pts)-3)),max(0,math.floor(min(p[1] for p in pts)-3)),min(W,math.ceil(max(p[0] for p in pts)+3)),min(H,math.ceil(max(p[1] for p in pts)+3)))
def layout(crops,density):
 rects=[];y=1;w=max(3*len(crops),max((x1-x0)*density for x0,y0,x1,y1 in crops))
 for x0,y0,x1,y1 in crops:
  cw=(x1-x0)*density;ch=(y1-y0)*density
  rects.append([0,y,x0*density,y0*density,cw,ch,density]);y+=ch
 if w>1024 or y>1024:raise ValueError('finite metadata/texture bounds')
 return w,y,rects

def choose(crops,budget,color=False):
 if type(budget)!=int or budget<0:raise ValueError('invalid byte budget')
 for mode,d in ([(2,1)] if color else [(1,4),(0,1)]):
  w,h,rects=layout(crops,d)
  if w*h*16<=budget:return dict(mode=mode,density=d,width=w,height=h,rects=rects,payload_bytes=w*h*16,budget=budget)
 raise ValueError('texture payload budget cannot fit bitmap fallback')
def pack(plan,sources):
 if len(sources)!=len(plan['rects']):raise ValueError('source count mismatch')
 if any(len(src)!=65*49*4*plan['density']**2 for src in sources):raise ValueError('source length mismatch')
 w,h=plan['width'],plan['height'];data=[0.]*(w*h*4);d=plan['density'];sw=65*d
 for g,(rect,src) in enumerate(zip(plan['rects'],sources)):
  x,y,ox,oy,cw,ch,_=rect
  for yy in range(ch):
   start=((oy+yy)*sw+ox)*4;dest=((y+yy)*w+x)*4;data[dest:dest+cw*4]=src[start:start+cw*4]
  data[12*g:12*g+4]=[n/1024 for n in (x,y,ox,oy)]
  data[12*g+4:12*g+8]=[n/1024 for n in (cw,ch,d,plan['mode'])]
 if len(data)!=w*h*4:raise ValueError('packed output size')
 return data
