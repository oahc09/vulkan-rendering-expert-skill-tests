#!/usr/bin/env python3
"""Progressive screen-space curve tessellation and real triangle draw experiment."""
import argparse,importlib.util,json,subprocess,sys,struct,math,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
SCALES=[.5+i/16 for i in range(11)]
PATH=[('M',12,30),('Q',32,4,52,30),('L',52,40),('L',12,40),('Z',)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def transform_point(x,y,scale):return ((x-32)*scale+32.25,(y-28)*scale+28.25)
def reference(scale,x,y):
 # Analytic original curve, not triangulator output: t=(x-12)/40,
 # quadratic y=30-52*t*(1-t), plus three straight boundary edges.
 xx=(x-32.25)/scale+32;yy=(y-28.25)/scale+28
 t=(xx-12)/40;cy=30-52*t*(1-t)
 inside=12<=xx<=52 and cy<=yy<=40
 # Conservative fixed .25 screen-pixel guard around the analytic boundary;
 # only this finite curve/slope range is covered. All excluded pixels reported.
 margin=.25/scale
 near=(12-margin<=xx<=52+margin and abs(yy-cy)<=margin) or (30-margin<=yy<=40+margin and min(abs(xx-12),abs(xx-52))<=margin) or (12-margin<=xx<=52+margin and abs(yy-40)<=margin)
 return float(inside),near

def distance(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def verify(folder,scale):
 data=(folder/'color.rgba32f').read_bytes()
 if len(data)!=W*H*16:raise ValueError('readback size')
 rgba=struct.unpack('<12740f',data)
 if not all(math.isfinite(v) for v in rgba):raise ValueError('nonfinite readback')
 reliable=[];edge=[];mismatches=0
 for y in range(H):
  for x in range(W):
   cov,near=reference(scale,x+.5,y+.5);a=cov*.75
   err=max(abs(rgba[(y*W+x)*4+c]-((a if c==3 else (.9,.5,.2)[c]*a)+(.1,.2,.3,.5)[c]*(1-a))) for c in range(4))
   (edge if near else reliable).append(err)
   mismatches+=err>1e-6
 if max(reliable)>1e-6:raise ValueError('analytic off-boundary composition mismatch')
 for name,v in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  b=(folder/(name+'.rgba32f')).read_bytes()
  if len(b)!=W*H*16 or any(x!=v[i%4] for i,x in enumerate(struct.unpack('<12740f',b))):raise ValueError('sentinel mismatch')
 return dict(scale=scale,max_off_boundary_error=max(reliable),reported_guard_pixels=len(edge),guard_max_error=max(edge,default=0),all_mismatch_pixels=mismatches)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 (out/'conditions.json').write_text(json.dumps(dict(scales=SCALES,phase=.25,flatten_tolerance=.125,analytic_guard=.25,off_boundary_blend_tolerance=1e-6,acceptance='finite progressive curve geometry, not antialiasing or arbitrary path quality')))
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 mesh=HERE.parent/'text_vector_mesh_lab';run('prepare',[sys.executable,mesh/'run_lab.py','--out',out/'prepared']);build=out/'prepared/prepared/build'
 q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad');sys.path.insert(0,str(ROOT/'tests'))
 from bounded_vector_mesh import triangulate
 rows=[];q.raw(out/'atlas.f32',[1.]*(W*H))
 for k,scale in enumerate(SCALES):
  points,tris=triangulate([PATH],transform=(scale,0,0,scale,32.25-32*scale,28.25-28*scale))
  # Dense analytic curve samples bound this finite curve's actual flattened edge
  # discrepancy. This is a sampled diagnostic, not a proof for all Beziers.
  err=max(min(distance(transform_point(12+40*t,30-52*t*(1-t),scale),u,v) for u,v in zip(points,points[1:]+points[:1])) for t in [i/1000 for i in range(1001)])
  if err>.125:raise ValueError('screen flatten bound')
  vertices=[]
  for tri in tris:
   for i in tri:
    x,y=points[i];vertices.extend([2*x/W-1,2*y/H-1,.5,.5])
  q.raw(out/('vertices-'+str(k)+'.f32'),vertices)
  folder=out/('frame-'+str(k));log=run('frame-'+str(k),[build/'mesh',build/'shaders',out/'atlas.f32',out/('vertices-'+str(k)+'.f32'),folder])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  row=verify(folder,scale);row.update(vertices=len(points),triangles=len(tris),dense_curve_error=err);rows.append(row)
 # Actual stale geometry from a different scale must not pass current reference.
 try:verify(out/'frame-0',SCALES[-1])
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('stale scale undetected')
 summary=dict(status='BOUNDED_PASS',rows=rows,negative='actual stale-scale GPU readback rejects',draws=len(rows),limits=['hard center samples; boundary guard reported not hidden','dense curve diagnostic not general proof','one curve with finite affine progressive scales','no temporal antialiasing/production cache or target GPU/Live qualification'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'run_lab.py',ROOT/'tests/bounded_vector_mesh.py',ROOT/'tests/bounded_vector_mask.py']},baseline_receipt='prepared/prepared/local-provenance.json'),indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
