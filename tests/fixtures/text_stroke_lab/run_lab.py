#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];GUARD=.01;TOL=1e-6
CASES=[{'name':c,'points':[(10.25,12.25),(30.25,12.25)],'width':6.,'cap':c,'join':'bevel','miter_limit':2.} for c in ['butt','square','round']]+[{'name':name,'points':[(12.25,30.25),(32.25,12.25),(40.25,36.25)],'width':8.,'cap':'butt','join':join,'miter_limit':limit} for name,join,limit in [('bevel','bevel',2.),('miter-limited','miter',1.5),('miter-accepted','miter',3.)]]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dist(p,a,b):
 d=(b[0]-a[0],b[1]-a[1]);den=d[0]**2+d[1]**2;t=max(0,min(1,((p[0]-a[0])*d[0]+(p[1]-a[1])*d[1])/den)) if den else 0
 return math.hypot(p[0]-a[0]-t*d[0],p[1]-a[1]-t*d[1])
def oracle(case,x,y):
 # Analytic segment projection and circular cap, not emitted mesh triangles.
 point=(x,y);points=case['points'];radius=case['width']/2;covered=False;boundary=[];directions=[]
 for index,(a,b) in enumerate(zip(points,points[1:])):
  length=math.dist(a,b);u=((b[0]-a[0])/length,(b[1]-a[1])/length);directions.append(u);along=(x-a[0])*u[0]+(y-a[1])*u[1];across=(x-a[0])*(-u[1])+(y-a[1])*u[0]
  lo=-radius if case['cap']=='square' and index==0 else 0;hi=length+radius if case['cap']=='square' and index==len(points)-2 else length
  covered|=lo<=along<=hi and abs(across)<=radius
  corners=[(a[0]+u[0]*t-u[1]*s,a[1]+u[1]*t+u[0]*s) for t,s in [(lo,-radius),(hi,-radius),(hi,radius),(lo,radius)]]
  boundary.extend(dist(point,c,d) for c,d in zip(corners,corners[1:]+corners[:1]))
 if case['cap']=='round':
  for center in [points[0],points[-1]]:
   d=math.dist(point,center);covered|=d<=radius;boundary.append(abs(d-radius))
 if len(points)==3:
  u,v=directions;turn=u[0]*v[1]-u[1]*v[0];dot=u[0]*v[0]+u[1]*v[1]
  if abs(turn)>1e-8:
   s=1 if turn>0 else -1;n1=(s*u[1],-s*u[0]);n2=(s*v[1],-s*v[0]);b=points[1];a=(b[0]+radius*n1[0],b[1]+radius*n1[1]);c=(b[0]+radius*n2[0],b[1]+radius*n2[1]);ratio=math.sqrt(2/(1+dot));tip=(b[0]+radius*(n1[0]+n2[0])/(1+dot),b[1]+radius*(n1[1]+n2[1])/(1+dot));polygon=[b,a,tip,c] if case['join']=='miter' and ratio<=case['miter_limit'] else [b,a,c]
   # Convex analytic join region via oriented half planes, no triangle decomposition.
   signs=[(d[0]-c0[0])*(y-c0[1])-(d[1]-c0[1])*(x-c0[0]) for c0,d in zip(polygon,polygon[1:]+polygon[:1])]
   covered|=all(k>=0 for k in signs) or all(k<=0 for k in signs);boundary.extend(dist(point,c0,d) for c0,d in zip(polygon,polygon[1:]+polygon[:1]))
 return covered,min(boundary)<=GUARD

def verify(folder,case):
 def read(name,n):
  data=(folder/(name+'.f32')).read_bytes()
  if len(data)!=n*4:raise ValueError('readback size')
  v=struct.unpack('<'+'f'*n,data)
  if not all(math.isfinite(x) for x in v):raise ValueError('nonfinite')
  return v
 rgba=read('color',12740);depth=read('depth',3185);outside=allmax=guardmax=0;excluded=[];covered=0
 for y in range(49):
  for x in range(65):
   inside,guard=oracle(case,x+.5,y+.5);i=y*65+x;expected=(.9,.2,.1,1) if inside else (.1,.2,.3,1);error=max(abs(rgba[4*i+c]-expected[c]) for c in range(4));de=abs(depth[i]-(.2 if inside else 1.));error=max(error,de);allmax=max(allmax,error);covered+=inside
   if guard:excluded.append({'x':x,'y':y,'max_color_depth_error':error});guardmax=max(guardmax,error)
   else:outside=max(outside,error)
 for name,c in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=c[i%4] for i,v in enumerate(read(name,12740))):raise ValueError('sentinel mismatch')
 if outside>TOL:raise ValueError('stroke composition outside boundary guard')
 return {'name':case['name'],'tolerance':TOL,'guard_pixels':GUARD,'excluded_count':len(excluded),'excluded_all_errors':excluded,'max_all_pixel_color_depth_error':allmax,'max_excluded_error':guardmax,'max_unexcluded_error':outside,'analytic_covered_pixels':covered}

def negative_visibility():
 rows=[]
 for name,actual,expected in [('wrong-cap',CASES[1],CASES[0]),('ignored-miter-limit',CASES[5],CASES[4])]:
  n=0
  for y in range(49):
   for x in range(65):
    a,ag=oracle(actual,x+.5,y+.5);e,eg=oracle(expected,x+.5,y+.5)
    n+=int(a!=e and not ag and not eg)
  if not n:raise ValueError('invisible legal negative before GPU')
  rows.append({'case':name,'analytic_mismatch_pixels_outside_both_guards':n})
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);stroke=load(HERE/'stroke.py','stroke')
 (out/'conditions.json').write_text(json.dumps({'cases':CASES,'boundary_guard_pixels':GUARD,'round_segments':stroke.CAP_STEPS,'max_circle_sagitta':4*(1-math.cos(math.pi/stroke.CAP_STEPS)),'tolerance':TOL,'miter_ratio_definition':'distance vertex to miter / half-width; <=limit keeps miter, >limit bevel','fixed_raster_boundary_reserve':.005,'negative_visibility_preflight':negative_visibility(),'guard_scope':'all analytic primitive boundaries, conservative also internal union edges; excluded errors fully reported'},indent=2))
 negatives=[('negative width',dict(width=-1)),('nonfinite width',dict(width=float('nan'))),('nonfinite point',dict(points=[(float('nan'),1),(2,3)])),('zero segment',dict(points=[(1,1),(1,1)])),('curves',dict(path_kind='quadratic')),('dash',dict(dash=[1,1])),('budget',dict(max_triangles=1))];rejected=[]
 base={k:v for k,v in CASES[0].items() if k!='name'}
 for name,override in negatives:
  try:stroke.generate(**dict(base,**override))
  except ValueError as e:
   expected={'negative width':'width budget','nonfinite width':'width budget','nonfinite point':'finite points','zero segment':'zero segment','curves':'unsupported curve/dash','dash':'unsupported curve/dash','budget':'triangle budget'}[name]
   if str(e)!=expected:raise
   rejected.append({'case':name,'reason':str(e)})
  else:raise ValueError('bad input accepted')
 if (out/'prepared').exists():raise ValueError('GPU started before input rejects')
 vertices={};meta={}
 for case in CASES:
  triangles,receipt=stroke.generate(**{k:v for k,v in case.items() if k!='name'});vertices[case['name']]=triangles;meta[case['name']]=receipt
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 extr=HERE.parent/'text_extrusion_lab';run('prepare',[sys.executable,extr/'run_lab.py','--out',out/'prepared']);build=out/'prepared/prepared/build';rows=[]
 def draw(name,triangles):
  values=[v for tri in triangles for x,y in tri for v in (x,y,0.,.9,.2,.1)];f=out/(name+'.vertices');f.write_bytes(struct.pack('<'+'f'*len(values),*values));log=run(name,[build/'extrusion',build/'shaders',f,out/name,'normal'])
  if 'validation_enabled=1' not in log:raise ValueError('validation')
 for case in CASES:draw(case['name'],vertices[case['name']]);rows.append(verify(out/case['name'],case))
 for name,actual,expected in [('wrong-cap',vertices['square'],CASES[0]),('ignored-miter-limit',vertices['miter-accepted'],CASES[4])]:
  draw(name,actual)
  try:verify(out/name,expected)
  except ValueError as e:
   if str(e)!='stroke composition outside boundary guard':raise
  else:raise ValueError('legal negative not detected')
 summary={'status':'BOUNDED_INTERIOR_PASS','validation_enabled':True,'cases':rows,'mesh_receipts':meta,'input_rejections_before_gpu':rejected,'actual_gpu_negatives':['wrong square cap for butt request','miter beyond declared limit instead of bevel'],'negative_visibility_preflight':negative_visibility(),'limits':['fixed screen-space simple polylines, opaque same-color union','round64-segment approximation; hard pixel centers not AA','guard exclusions explicitly reported, not full-boundary pixel qualification','no curves/dashes/general stroke/SVG/font text','no target device or Live acceptance']};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'run_lab.py',HERE/'stroke.py',extr/'run_lab.py',extr/'main.cpp',extr/'extrude.vert',extr/'extrude.frag']},'prepared_receipt':json.loads((out/'prepared/local-provenance.json').read_text()),'generated_vertices':{p.name:sha(p) for p in out.glob('*.vertices')}},indent=2))
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','preview')
 for case in CASES:
  v=struct.unpack('<12740f',(out/case['name']/'color.f32').read_bytes());preview.png(out/case['name']/'preview.png',65,49,bytes(round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for i,x in enumerate(v) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
