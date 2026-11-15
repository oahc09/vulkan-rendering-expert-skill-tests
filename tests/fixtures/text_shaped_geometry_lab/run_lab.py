#!/usr/bin/env python3
"""Fixed shaped-GlyphID -> bounded extrusion or actual hole-preserving bitmap."""
import argparse,hashlib,importlib.util,json,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
FONT_SHA='57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e'
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def paths(contours):
 result=[]
 for contour in contours:
  q=[('M',*contour[0][0])]
  for edge in contour:
   if len(edge)==2:q.append(('L',*edge[-1]))
   elif len(edge)==3:q.append(('Q',*edge[1],*edge[2]))
   elif len(edge)==4:q.append(('C',*edge[1],*edge[2],*edge[3]))
   else:raise ValueError('edge form')
  # Endpoint already equals start, but existing flattener uses Z to close.
  q.append(('Z',));result.append(q)
 return result

def closed_mesh(points,tris,colors):
 triangles=[]
 # All accepted mesh polygons are CCW in authored coordinates.
 area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))
 if area<=0:raise ValueError('unexpected contour winding')
 for z,kind in [(0,0),(6,1)]:
  for t in tris:triangles.append([(*points[i],z,*colors[kind]) for i in (t[::-1] if kind==0 else t)])
 for a,b in zip(points,points[1:]+points[:1]):
  q=[(*a,0),(*b,0),(*b,6),(*a,6)]
  for t in [(0,1,2),(0,2,3)]:triangles.append([(*q[i],*colors[2]) for i in t])
 edges={}
 for tri in triangles:
  for a,b in zip(tri,tri[1:]+tri[:1]):
   pair=(tuple(a[:3]),tuple(b[:3]));edges[pair]=edges.get(pair,0)+1
 if any(n!=1 or edges.get((b,a))!=1 for (a,b),n in edges.items()):raise ValueError('nonclosed oriented mesh')
 return [x for tri in triangles for v in tri for x in v],len(triangles)

def hole_pixels(mask):
 # Independent topology of the provider bitmap, not output GPU pixels.
 exterior=set();stack=[i for i,c in enumerate(mask) if c==0 and (i%65 in (0,64) or i//65 in (0,48))]
 while stack:
  i=stack.pop()
  if i in exterior:continue
  exterior.add(i);x,y=i%65,i//65
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   j=yy*65+xx
   if 0<=xx<65 and 0<=yy<49 and mask[j]==0 and j not in exterior:stack.append(j)
 return [i for i,c in enumerate(mask) if c==0 and i not in exterior]

def auxiliary_check(folder,suffix):
 for name,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  data=(folder/(name+suffix)).read_bytes()
  if len(data)!=12740*4:raise ValueError('auxiliary size')
  actual=struct.unpack('<12740f',data)
  if any(v!=values[i%4] for i,v in enumerate(actual)):raise ValueError('auxiliary sentinel mismatch')

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args()
 if not a.font.is_file() or a.font.stat().st_size!=759720 or sha(a.font)!=FONT_SHA:raise ValueError('fixed trusted font required before parsing')
 out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args,timeout=180):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 provider=load(HERE.parent/'text_msdf_lab/run_lab.py','outline_provider');bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');extrude=load(HERE.parent/'text_extrusion_lab/run_lab.py','extrude')
 sys.path.insert(0,str(ROOT/'tests'))
 try:from bounded_vector_mesh import triangulate
 finally:sys.path.pop(0)
 inputs={};receipts={};decisions={}
 for letter,gid,contour_count in [('L',47,1),('O',50,2),('F',41,1)]:
  contours,receipt=provider.outlines(a.font,letter)
  if len(contours)!=contour_count or [g['id'] for g in receipt['glyphs']]!=[gid]:raise ValueError('fixed shaping/outline identity changed')
  # Fixed quarter-pixel placement before any new GPU run avoids boundary-center ties.
  contours=[[[[x+.25,y+.25] for x,y in edge] for edge in contour] for contour in contours];inputs[letter]=contours;receipts[letter]=receipt
  if letter in ('L','F') and any(len(edge)!=2 for contour in contours for edge in contour):raise ValueError('straight contour subset')
  try:points,tris=triangulate(paths(contours));decision='finite_extrusion'
  except ValueError as e:
   if letter!='O' or str(e)!='holes/multiple contours require mask fallback':raise
   decision='planar_bitmap_fallback'
  decisions[letter]=decision
 if decisions!={'L':'finite_extrusion','O':'planar_bitmap_fallback','F':'finite_extrusion'}:raise ValueError('representation route changed')
 conditions={'font_sha256':FONT_SHA,'positive_glyph_ids':[47,50],'wrong_glyph_id':41,'routes':decisions,'outline_height':24,'outline_translation':[.25,.25],'extrusion_depth':6,'projection':'existing affine oblique x+z, y+.5z; depth .2+.05z','tolerance':1e-6,'mask_raster_size':20,'mask_position':'existing integer placement/baseline','fallback_not_equivalent_3d':True}
 (out/'conditions.json').write_text(json.dumps(conditions,indent=2));(out/'provider-receipts.json').write_text(json.dumps(receipts,indent=2));(out/'outlines.json').write_text(json.dumps(inputs))
 run('prepare-extrusion',[sys.executable,HERE.parent/'text_extrusion_lab/run_lab.py','--out',out/'prepared-extrusion'])
 eb=out/'prepared-extrusion/prepared/build';meshrows=[]
 # Independent ray reference operates on source outline, not ear-clipped triangles.
 extrude.P=[tuple(edge[0]) for edge in inputs['L'][0]]
 for letter in ('L','F'):
  points,tris=triangulate(paths(inputs[letter]));vertices,triangles=closed_mesh(points,tris,extrude.COLORS)
  vf=out/(letter+'.vertices');vf.write_bytes(struct.pack('<'+'f'*len(vertices),*vertices));log=run('draw-'+letter,[eb/'extrusion',eb/'shaders',vf,out/(letter+'-gpu'),'normal'])
  if 'validation_enabled=1' not in log:raise ValueError('mesh validation')
  if letter=='L':row=extrude.verify(out/'L-gpu');row.update(glyph_id=47,triangles=triangles);meshrows.append(row)
  else:
   auxiliary_check(out/'F-gpu','.f32')
   try:extrude.verify(out/'F-gpu')
   except ValueError as e:
    if 'extrusion color/depth mismatch' not in str(e):raise
   else:raise ValueError('wrong shaped glyph accepted')
 run('prepare-bitmap',[sys.executable,HERE.parent/'text_bitmap_lab/run_lab.py','--out',out/'prepared-bitmap','--font',a.font])
 bb=out/'prepared-bitmap/build';mask,raster_receipt=bitmap.raster(a.font,'O','ltr','en',pixel_size=20)
 if [g['id'] for g in raster_receipt['glyphs']]!=[50] or raster_receipt['font_sha256']!=FONT_SHA:raise ValueError('fallback changed glyph/face')
 holes=hole_pixels(mask)
 if not holes:raise ValueError('no independent enclosed hole pixels')
 (out/'fallback-receipt.json').write_text(json.dumps(raster_receipt,indent=2));folder=out/'O-fallback';folder.mkdir();(folder/'mask.f32').write_bytes(struct.pack('<3185f',*mask))
 log=run('draw-fallback',[bb/'bitmap_lab',bb/'shaders',folder/'mask.f32',folder/'gpu'])
 if 'validation_enabled=1' not in log:raise ValueError('fallback validation')
 fallback=bitmap.verify(folder);rgba=struct.unpack('<12740f',(folder/'gpu/color.rgba32f').read_bytes())
 if any(abs(rgba[i*4+c]-(.1,.2,.3,.5)[c])>1e-6 for i in holes for c in range(4)):raise ValueError('hole not preserved')
 wrongmask=mask.copy()
 for i in holes:wrongmask[i]=1.
 wf=out/'filled-hole.f32';wf.write_bytes(struct.pack('<3185f',*wrongmask));bad=out/'O-filled';bad.mkdir();shutil.copyfile(folder/'mask.f32',bad/'mask.f32');run('draw-wrong-filled',[bb/'bitmap_lab',bb/'shaders',wf,bad/'gpu'])
 auxiliary_check(bad/'gpu','.rgba32f')
 try:bitmap.verify(bad)
 except ValueError as e:
  if str(e)!='composition mismatch':raise
 else:raise ValueError('forced solid fallback accepted')
 summary={'status':'PASS','validation_enabled':True,'positive_routes':{'L':'shaped glyph47 actual front/back/side mesh','O':'shaped glyph50 multiple contours rejected then actual planar bitmap fallback'},'mesh':meshrows,'fallback':fallback,'enclosed_hole_pixels':len(holes),'negative_checks':['actual F glyph41 mesh rejected against L source outline','actual forced hole-fill GPU output rejected'],'limits':['fixed trusted Linux font/provider and two positive glyphs','outline no-scale normalized height24, planar fallback independently uses existing20px hinted bitmap placement','fallback explicit flat representation, not depth/shadow equivalence to solid glyph','no bevel, lighting/shadows/second view, general world labels','mesh active MRT/depth; planar mask UNUSED preservation','font parser/shaping/raster quality not independently certified','target platform and semantic Live unverified']};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'run_lab.py',provider.HERE/'run_lab.py',bitmap.HERE/'run_lab.py',extrude.HERE/'run_lab.py',ROOT/'tests/bounded_vector_mesh.py']},'mesh_receipt':json.loads((out/'prepared-extrusion/local-provenance.json').read_text()),'bitmap_summary':json.loads((out/'prepared-bitmap/summary.json').read_text()),'inputs':{p.name:sha(p) for p in [out/'outlines.json',out/'L.vertices',out/'F.vertices',folder/'mask.f32',wf]}},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
