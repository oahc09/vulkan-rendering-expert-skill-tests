#!/usr/bin/env python3
"""Actual triangle-list draws from bounded concave outlines, independent fill oracle."""
import argparse,importlib.util,json,os,subprocess,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
P=[(8,8),(48,8),(48,40),(36,40),(36,20),(20,20),(20,40),(8,40)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def inside(x,y,points):
 result=False
 for a,b in zip(points,points[1:]+points[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
 return result

def verify(folder):return load(HERE.parent/'text_bitmap_lab/run_lab.py','oracle').verify(folder)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 quad=HERE.parent/'text_packed_quad_lab';run('prepare',[sys.executable,quad/'run_lab.py','--out',out/'prepared','--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']);build=out/'prepared/build'
 # Shared vertex-input pipeline is unchanged. Only the input triangle-list
 # divisibility guard differs from the old six-vertices-per-quad fixture.
 source=(quad/'main.cpp').read_text()
 if source.count('verts.size()%24')!=1:raise ValueError('source hook changed')
 (build/'mesh.cpp').write_text(source.replace('verts.size()%24','verts.size()%12'))
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
 if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('compile',cmd+[build/'mesh.cpp','-l:libvulkan.so.1','-o',build/'mesh'])
 q=load(quad/'run_lab.py','quad');sys.path.insert(0,str(ROOT/'tests'))
 from bounded_vector_mesh import triangulate,cross
 path=[('M',*P[0])]+[('L',*p) for p in P[1:]]+[('Z',)]
 rows=[]
 for label,transform in [('normal',(1,0,0,1,0,0)),('mirrored',(-1,0,0,1,64,0))]:
  points,triangles=triangulate([path],transform=transform);folder=out/label;folder.mkdir()
  q.raw(folder/'mask.f32',[float(inside(x+.5,y+.5,points)) for y in range(H) for x in range(W)])
  q.raw(folder/'atlas.f32',[1.]*(W*H))
  def draw(name,tris):
   vertices=[]
   for t in tris:
    for i in t:
     x,y=points[i];vertices.extend([2*x/W-1,2*y/H-1,.5,.5])
   q.raw(folder/(name+'.f32'),vertices)
   log=run(label+'-'+name,[build/'mesh',build/'shaders',folder/'atlas.f32',folder/(name+'.f32'),folder/name])
   if 'validation_enabled=1' not in log:raise ValueError('validation missing')
  draw('gpu',triangles);row=verify(folder);row.update(case=label,triangles=len(triangles),area=sum(abs(cross(*(points[i] for i in t)))/2 for t in triangles));rows.append(row)
  draw('fan',[(0,i,i+1) for i in range(1,len(points)-1)])
  # Oracle input stays original polygon, not triangles or a generated mask.
  bad=folder/'bad';bad.mkdir();(bad/'mask.f32').write_bytes((folder/'mask.f32').read_bytes());(bad/'gpu').symlink_to(folder/'fan',target_is_directory=True)
  try:verify(bad)
  except ValueError as e:
   if 'composition mismatch' not in str(e):raise
  else:raise ValueError('incorrect concave triangle fan undetected')
 summary={'status':'PASS','validation_enabled':True,'draws':4,'rows':rows,'negative_checks':['actual wrong fan draw rejected for each winding'],'scope':'one simple concave contour and mirrored winding; real vertex triangle lists; CPU point-in-polygon reference','limits':['hard pixel-center coverage only','holes/multiple contours explicitly reject to existing mask fallback','no stroke/extrusion/bevel/3D shadows','no target hardware/Live acceptance']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'head':run('head',['git','rev-parse','HEAD']),'status':run('status',['git','status','--porcelain']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'run_lab.py',ROOT/'tests/bounded_vector_mesh.py',ROOT/'tests/bounded_vector_mask.py',quad/'run_lab.py',quad/'main.cpp']},'binary':hashlib.sha256((build/'mesh').read_bytes()).hexdigest()},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
