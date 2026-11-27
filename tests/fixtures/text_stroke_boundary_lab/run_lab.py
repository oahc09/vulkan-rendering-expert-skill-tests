#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,math,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;TOL=1e-6

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def verify(folder,c,ref):
 def read(n,count):
  b=(folder/(n+'.f32')).read_bytes()
  if len(b)!=count*4:raise ValueError('size')
  v=struct.unpack('<'+'f'*count,b)
  if not all(math.isfinite(x) for x in v):raise ValueError('nonfinite')
  return v
 color=read('color',12740);depth=read('depth',3185)
 for name,s in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=s[i%4] for i,v in enumerate(read(name,12740))):raise ValueError('auxiliary mismatch')
 errors=[];maxerr=0;covered=0
 for y in range(49):
  for x in range(65):
   hit=ref.covered(c,x+.5,y+.5);covered+=hit;i=y*65+x;rgba=(.9,.2,.1,1) if hit else (.1,.2,.3,1);e=max(*(abs(color[4*i+k]-rgba[k]) for k in range(4)),abs(depth[i]-(.2 if hit else 1)))
   maxerr=max(maxerr,e)
   if e>TOL:errors.append(dict(x=x,y=y,error=e))
 return dict(name=c['name'],max_all_pixel_color_depth_error=maxerr,excluded_count=0,covered_pixels=covered,mismatch_pixels=errors)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 old=load(HERE.parent/'text_stroke_lab/run_lab.py','old');ref=load(HERE/'reference.py','ref');cases=old.CASES+[dict(c,name=c['name']+'-reverse',points=c['points'][::-1]) for c in old.CASES[3:]]
 agreement=[]
 for c in old.CASES:
  differences=[(x,y) for y in range(49) for x in range(65) if old.oracle(c,x+.5,y+.5)[0]!=ref.covered(c,x+.5,y+.5)]
  if differences:raise ValueError('old analytic reference coverage changed')
  agreement.append({'case':c['name'],'compared_pixels':3185,'different_coverage_pixels':len(differences)})
 conditions={'old_reference_coverage_agreement':agreement,'cases':cases,'tolerance':TOL,'excluded_count':0,'semantics':'closed analytic pixel-center coverage, opaque union','old_case_coordinates_unchanged':True,'new_path':'support quad plus analytic fragment discard; not pure stroke mesh','round':'analytic circle, not old64-gon'}
 (out/'conditions.json').write_text(json.dumps(conditions,indent=2))
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(n+' failed '+log[-1500:])
  return log
 # Preserve and reproduce original failure rather than overwrite its results.
 run('old-stroke',[sys.executable,HERE.parent/'text_stroke_lab/run_lab.py','--out',out/'old-stroke']);build=out/'old-stroke/prepared/prepared/build'
 helper=(build/'extrusion_helper.hpp').read_text()
 if 'fs=shader("coverage.frag")' not in helper:raise ValueError('fragment shader load name drift')
 src=(HERE.parent/'text_extrusion_lab/main.cpp').read_text();hook='TextLab lab(argv[1]);';assert src.count(hook)==1
 src=src.replace(hook,hook+'std::cout<<"subPixelPrecisionBits="<<lab.properties.limits.subPixelPrecisionBits<<"\\n";')
 (out/'main.cpp').write_text(src);run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',out/'main.cpp','-l:libvulkan.so.1','-o',out/'boundary'])
 # Fixed viewport support mesh. It is not the tessellated stroke contour.
 xy=[(0,0),(65,0),(65,49),(0,0),(65,49),(0,49)];data=[v for x,y in xy for v in (x,y,0,.9,.2,.1)];(out/'support.vertices').write_bytes(struct.pack('<36f',*data))
 template=(HERE/'coverage.frag').read_text();assert template.count('// CASE_CONSTANTS')==1
 shader_hashes={}
 def draw(name,c,open_end=False):
  folder=out/(name+'-shaders');folder.mkdir()
  for f in (build/'shaders').glob('*.spv'):shutil.copy2(f,folder/f.name)
  pts=c['points'];const='const int COUNT='+str(len(pts))+';\nconst vec2 POINTS[3]=vec2[]('+','.join('vec2('+str(float(x))+','+str(float(y))+')' for x,y in (pts+[pts[-1]]*(3-len(pts))))+');\n'
  const+=f"const float WIDTH={float(c['width'])},LIMIT={float(c['miter_limit'])};const int CAP={['butt','square','round'].index(c['cap'])};const bool MITER={str(c['join']=='miter').lower()},OPEN_END={str(open_end).lower()};"
  source=folder/'coverage.frag';source.write_text(template.replace('// CASE_CONSTANTS',const));run(name+'-compile',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',source,'-o',folder/'coverage.frag.spv']);run(name+'-spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',folder/'coverage.frag.spv']);shader_hashes[name]=hashlib.sha256((folder/'coverage.frag.spv').read_bytes()).hexdigest()
  log=run(name,[out/'boundary',folder,out/'support.vertices',out/name,'normal'])
  if 'validation_enabled=1' not in log:raise ValueError('validation missing')
  return log
 rows=[]
 for c in cases:
  draw(c['name'],c);row=verify(out/c['name'],c,ref)
  if row['max_all_pixel_color_depth_error']>TOL:raise ValueError('positive analytic coverage mismatch '+json.dumps(row))
  rows.append(row)
 negatives=[]
 for name,actual,expected,mode in [('wrong-cap',cases[1],cases[0],False),('ignored-miter-limit',cases[5],cases[4],False),('open-endpoint',cases[3],cases[3],True)]:
  draw(name,actual,mode);r=verify(out/name,expected,ref)
  if not r['mismatch_pixels']:raise ValueError('invisible negative '+name)
  negatives.append(dict(name=name,**{k:v for k,v in r.items() if k!='name'}))
 original=[]
 for c in cases[3:6]:
  r=verify(out/'old-stroke'/c['name'],c,ref)
  if not r['mismatch_pixels']:raise ValueError('original boundary failure unexpectedly absent')
  original.append(r)
 bits=int(next(line.split('=')[1] for line in (out/'bevel.log').read_text().splitlines() if line.startswith('subPixelPrecisionBits=')))
 # Model-only diagnostic: original terminal offset points vs nearest reported-grid snapping.
 a,b=old.CASES[3]['points'][-2:];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);r=old.CASES[3]['width']/2
 endpoint=[(b[0]-dy*r/length,b[1]+dx*r/length),(b[0]+dy*r/length,b[1]-dx*r/length)]
 grid=2**bits;snap=[(round(x*grid)/grid,round(y*grid)/grid) for x,y in endpoint]
 diag=[]
 rgba=struct.unpack('<12740f',(out/'old-stroke/bevel/color.f32').read_bytes())
 for x,y in [(42,35),(39,36),(36,37)]:
  q=(x+.5,y+.5);edge=(snap[1][0]-snap[0][0],snap[1][1]-snap[0][1]);diag.append({'x':x,'y':y,'exact_terminal_dot':(q[0]-b[0])*dx+(q[1]-b[1])*dy,'snapped_edge_cross_model':edge[0]*(q[1]-snap[0][1])-edge[1]*(q[0]-snap[0][0]),'actual_original_mesh_covered':rgba[4*(y*65+x)]>.5})
 diagnostic={'reported_subpixel_precision_bits':bits,'endpoint_float64':endpoint,'nearest_grid_model':snap,'samples':diag,'scope':'nearest-grid model explains split; not proof of driver snapping algorithm or Vulkan-wide top-left rule'}
 summary={'old_reference_coverage_agreement':agreement,'boundary_diagnostic':diagnostic,'status':'BOUNDED_ANALYTIC_FALLBACK_PASS','tolerance':TOL,'validation_enabled':True,'cases':rows,'actual_gpu_negatives':negatives,'omitted_fallback_original_mesh':original,'limits':['same configured software Vulkan only','closed hard pixel-center opaque coverage; not AA or transparent blending','support mesh plus analytic fragment fallback, not pure mesh precision repair','fixed straight and2segmentpaths; no curves/dashes/generalSVG']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'sources':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [HERE/'run_lab.py',HERE/'reference.py',HERE/'coverage.frag',HERE.parent/'text_stroke_lab/run_lab.py']},'binary':hashlib.sha256((out/'boundary').read_bytes()).hexdigest(),'shaders':shader_hashes,'old_provenance':json.loads((out/'old-stroke/local-provenance.json').read_text())},indent=2))
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','png')
 for c in cases:
  v=struct.unpack('<12740f',(out/c['name']/'color.f32').read_bytes());preview.png(out/c['name']/'preview.png',65,49,bytes(round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for i,x in enumerate(v) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
