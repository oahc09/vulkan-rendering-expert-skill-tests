import argparse,importlib.util,json,math,os,struct,subprocess,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];TOL=1e-6

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def hit(poly,x,y,k,l):
 def cross(a,b):return a[0]*b[1]-a[1]*b[0]
 def inside(p,poly):
  xx,yy=p;yes=False
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if (a[1]>yy)!=(b[1]>yy) and xx<(b[0]-a[0])*(yy-a[1])/(b[1]-a[1])+a[0]:yes=not yes
  return yes
 hits=[]
 for z in (0,6):
  if inside((x-k*z,y-l*z),poly):hits.append((z,'cap'))
 for a,b in zip(poly,poly[1:]+poly[:1]):
  e=(b[0]-a[0],b[1]-a[1]);den=cross((k,l),e)
  if not den:continue
  z=cross((x-a[0],y-a[1]),e)/den;u=((x-k*z-a[0])*e[0]+(y-l*z-a[1])*e[1])/(e[0]**2+e[1]**2)
  if 0<=z<=6 and 0<=u<=1:hits.append((z,'side'))
 return min(hits) if hits else None

def reference(poly,g,shadow,k,l):
 color=[];depth=[];roi=dict(cap=0,side=0,shadow=0,label_visible=0,label_hidden=0)
 for y in range(49):
  for x in range(65):
   px=x+.5;py=y+.5;wx=px-k*10;wy=py-l*10;sx=math.floor(wx+5);sy=math.floor(wy+2.5);blocked=0<=sx<65 and 0<=sy<49 and .625>shadow[sy*65+sx]
   c=[v*(.25 if blocked else 1) for v in (.8,.6,.4)]+[1];z=10;kind='shadow' if blocked else None
   h=hit(poly,px,py,k,l)
   if h:z,kind=h;c=[.2,.6,.8,1]
   if 34<=px-k<43 and 17<=py-l<28 and 1<z:z=1;kind=None;c=[.3,.25,.5,1]
   if kind:roi[kind]+=1
   gx=px-k*3-32;gy=py-l*3-15
   if 0<=gx<14 and 0<=gy<15:
    a=g[math.floor(gy)*14+math.floor(gx)]*.75
    if a:
     roi['label_visible' if 3<z else 'label_hidden']+=1
     if 3<z:c=[v*a+c[i]*(1-a) for i,v in enumerate((.9,.3,.1,1))]
   color.extend(c);depth.append(z/16)
 return color,depth,roi

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False,parents=True)
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(n+' failed '+log[-1800:])
  return log
 source=load(HERE.parent/'text_msdf_lab/run_lab.py','outline');shape=load(HERE.parent/'text_shaped_geometry_lab/run_lab.py','shape');bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');old=load(HERE.parent/'text_shadow_lab/run_lab.py','shadow')
 if a.font.stat().st_size!=759720 or hashlib.sha256(a.font.read_bytes()).hexdigest()!=old.FONT_SHA:raise ValueError('trusted font')
 contours,receipt=source.outlines(a.font,'L');assert [g['id'] for g in receipt['glyphs']]==[47]
 if receipt['font_sha256']!=old.FONT_SHA or receipt['missing_glyphs']:raise ValueError('L provider identity')
 if len(contours)!=1 or len(contours[0])!=6 or any(len(edge)!=2 for edge in contours[0]):raise ValueError('finite L straight contour subset')
 contours=[[[[x+.25,y+.25] for x,y in edge] for edge in c] for c in contours];poly=[tuple(e[0]) for e in contours[0]]
 sys.path.insert(0,str(ROOT/'tests'));from bounded_vector_mesh import triangulate
 q,t=triangulate(shape.paths(contours));verts,count=shape.closed_mesh(q,t,[(1,1,1)]*3);assert count==20
 mask,oreceipt=bitmap.raster(a.font,'O','ltr','en');assert [g['id'] for g in oreceipt['glyphs']]==[50] and not oreceipt['clipped_samples']
 if oreceipt['font_sha256']!=old.FONT_SHA or oreceipt['missing_glyphs']:raise ValueError('O provider identity')
 xy=[(i%65,i//65) for i,v in enumerate(mask) if v];x0=min(x for x,y in xy);x1=max(x for x,y in xy)+1;y0=min(y for x,y in xy);y1=max(y for x,y in xy)+1;assert (x1-x0,y1-y0)==(14,15)
 g=[mask[y*65+x] for y in range(y0,y1) for x in range(x0,x1)];page=[0.]*3185
 for y in range(15):page[y*65:y*65+14]=g[y*14:y*14+14]
 shadow=old.shadow_reference(poly);refs={n:reference(poly,g,shadow,k,l) for n,k,l in [('A',.25,.125),('B',-.25,.25)]}
 (out/'preflight.json').write_text(json.dumps({n:r[2] for n,r in refs.items()},indent=2))
 if not all(all(v>0 for v in r[2].values()) for r in refs.values()):raise ValueError('non-observable frozen scene')
 (out/'mesh.f32').write_bytes(struct.pack('<'+'f'*len(verts),*verts));(out/'mask.f32').write_bytes(struct.pack('<3185f',*page));(out/'provider.json').write_text(json.dumps([receipt,oreceipt],indent=2))
 b=load(HERE/'build.py','builder').build(out,run);log=run('actual',[b/'scene',b/'shaders',out/'mesh.f32',out/'mask.f32',out/'gpu'])
 if 'validation_enabled=1' not in log:raise ValueError('validation receipt')
 (out/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*'),HERE.parent/'text_shadow_lab/main.cpp',HERE.parent/'text_shadow_lab/shadow.vert',HERE.parent/'text_active_mrt_lab/run_lab.py',HERE.parent/'text_msdf_lab/run_lab.py',HERE.parent/'text_bitmap_lab/run_lab.py',HERE.parent/'text_shaped_geometry_lab/run_lab.py',ROOT/'tests/bounded_vector_mesh.py',b/'scene'] if p.is_file()},indent=2))
 actualshadow=old.floats(out/'gpu/shadow.f32',3185);se=max(abs(x-y) for x,y in zip(actualshadow,shadow));rows={}
 for n in ['A','B','B-no-shadow','B-stale-label']:
  d=out/'gpu'/n;ref=refs['A' if n=='A' else 'B'];c=old.floats(d/'color.f32',12740);z=old.floats(d/'depth.f32',3185)
  for name,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
   if any(v!=values[i%4] for i,v in enumerate(old.floats(d/(name+'.f32'),12740))):raise ValueError('aux')
  de=max(abs(x-y) for x,y in zip(z,ref[1]));ce=max(abs(x-y) for x,y in zip(c,ref[0]));rows[n]=dict(color_error=ce,depth_error=de,roi=ref[2]);assert de<=TOL
  # Diagnostic PNG only, never source input.
  import zlib
  raw=b''.join(b'\0'+bytes(round(max(0,min(1,c[(y*65+x)*4+j]))*255) for x in range(65) for j in range(3)) for y in range(49))
  def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v))
  (d/'preview.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',65,49,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
 ok=se<=TOL and all(rows[n]['color_error']<=TOL for n in ['A','B']) and all(rows[n]['color_error']>TOL for n in ['B-no-shadow','B-stale-label'])
 summary=dict(status='PASS' if ok else 'NOT_QUALIFIED',validation_enabled=True,shadow_depth_error=se,cases=rows,tolerance=TOL,excluded=0,device_count=1,positive_views=2,negative_views=2,scene_draws_per_view=4)
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
 if not ok:raise ValueError('shared scene numerical gate')
if __name__=='__main__':main()
