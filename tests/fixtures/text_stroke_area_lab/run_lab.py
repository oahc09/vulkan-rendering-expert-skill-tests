#!/usr/bin/env python3
import argparse,importlib.util,json,math,os,struct,subprocess,sys,hashlib,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;TOL=1e-6
# Registered before first run: exact rectangles only, 4 quarter-pixel phases.
CASES=[dict(name=f'{direction}-{cap}-{phase}',points=[(10.25+phase/4,12.25+phase/4),(30.25+phase/4,12.25+phase/4)] if direction=='horizontal' else [(10.25+phase/4,12.25+phase/4),(30.25+phase/4,27.25+phase/4)],width=5.,cap=cap) for direction in ('horizontal','diagonal') for cap in ('butt','square') for phase in range(4)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def verify(path,c,ref):
 def read(n,count):
  b=(path/(n+'.f32')).read_bytes()
  if len(b)!=count*4:raise ValueError('readback size')
  v=struct.unpack('<'+'f'*count,b)
  if not all(math.isfinite(a) for a in v):raise ValueError('nonfinite')
  return v
 col=read('color',12740);dep=read('depth',3185)
 for name,s in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(a!=s[i%4] for i,a in enumerate(read(name,12740))):raise ValueError('auxiliary mismatch')
 comp=ce=roi=edge_error=depth_error=0.;n=partial=0
 for y in range(49):
  for x in range(65):
   coverage=float(ref.area(c,x,y));alpha=.75*coverage;expected=[.9*alpha+.1*(1-alpha),.2*alpha+.2*(1-alpha),.1*alpha+.3*(1-alpha),alpha+.5*(1-alpha)];i=y*65+x
   error=max(abs(col[4*i+k]-expected[k]) for k in range(4));comp=max(comp,error);depth_error=max(depth_error,abs(dep[i]-1))
   inferred=(col[4*i+3]-.5)/.375;ce=max(ce,abs(inferred-coverage))
   if coverage>0:n+=1;roi=max(roi,error)
   partial+=0<coverage<1
   if 0<coverage<1:edge_error=max(edge_error,abs(inferred-coverage))
 if depth_error>TOL:raise ValueError('depth preservation mismatch')
 return dict(name=c['name'],max_depth_preservation_error=depth_error,max_composition_depth_error=comp,max_alpha_inferred_coverage_error=ce,stroke_roi_pixels=n,partial_pixels=partial,max_stroke_roi_composition_error=roi,max_partial_pixel_coverage_error=edge_error,excluded_count=0)

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);ref=load(HERE/'reference.py','area_ref')
 (out/'conditions.json').write_text(json.dumps(dict(cases=CASES,composition_tolerance=TOL,area_tolerance=TOL,area_gate_origin='new preregistered bounded exact-rectangle experiment, not original plan global quality gate',coverage_reference='exact rational vertical integration',opacity=.75,background=[.1,.2,.3,.5],excluded_count=0),indent=2))
 def run(n,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(n+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(n+' failed '+log[-1000:])
  return log
 extr=HERE.parent/'text_extrusion_lab';run('prepare',[sys.executable,extr/'run_lab.py','--out',out/'prepared']);build=out/'prepared/prepared/build'
 source=(extr/'main.cpp').read_text();hook='{.1f,.2f,.3f,1}';assert source.count(hook)==1;source=source.replace(hook,'{.1f,.2f,.3f,.5f}');(out/'main.cpp').write_text(source)
 helper=(build/'extrusion_helper.hpp').read_text();assert 'fs=shader("coverage.frag")' in helper
 assert helper.count('ds.depthWriteEnable=VK_TRUE;')==1
 (build/'extrusion_helper.hpp').write_text(helper.replace('ds.depthWriteEnable=VK_TRUE;','ds.depthWriteEnable=VK_FALSE;'))
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',out/'main.cpp','-l:libvulkan.so.1','-o',out/'area'])
 xy=[(0,0),(65,0),(65,49),(0,0),(65,49),(0,49)];(out/'support.vertices').write_bytes(struct.pack('<36f',*[v for x,y in xy for v in (x,y,0,.9,.2,.1)]))
 template=(HERE/'coverage.frag').read_text();assert template.count('// CONSTANTS')==1
 def draw(name,c,hard=False,double=False):
  # Producer uses floating Euclidean path normalization; oracle uses rational direction.
  a,b=c['points'];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);u=(dx/length,dy/length);r=c['width']/2
  if c['cap']=='square':a=(a[0]-r*u[0],a[1]-r*u[1]);b=(b[0]+r*u[0],b[1]+r*u[1])
  normal=(-r*u[1],r*u[0]);q=[(a[0]+normal[0],a[1]+normal[1]),(b[0]+normal[0],b[1]+normal[1]),(b[0]-normal[0],b[1]-normal[1]),(a[0]-normal[0],a[1]-normal[1])]
  folder=out/(name+'-shaders');folder.mkdir()
  for f in (build/'shaders').glob('*.spv'):shutil.copy2(f,folder/f.name)
  const='const vec2 CORNERS[4]=vec2[]('+','.join(f'vec2({x},{y})' for x,y in q)+');\n'+f'const bool HARD={str(hard).lower()},DOUBLE_ALPHA={str(double).lower()};'
  shader=folder/'coverage.frag';shader.write_text(template.replace('// CONSTANTS',const));run(name+'-compile',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',shader,'-o',folder/'coverage.frag.spv']);run(name+'-spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',folder/'coverage.frag.spv']);log=run(name,[out/'area',folder,out/'support.vertices',out/name,'normal'])
  if 'validation_enabled=1' not in log:raise ValueError('validation missing')
 rows=[]
 for c in CASES:
  draw(c['name'],c);r=verify(out/c['name'],c,ref)
  if r['max_composition_depth_error']>TOL or r['max_alpha_inferred_coverage_error']>TOL:raise ValueError('area oracle mismatch '+json.dumps(r))
  rows.append(r)
 sequence=[]
 for group in range(4):
  block=CASES[group*4:group*4+4];worst=0.
  for previous,current in zip(block,block[1:]):
   pcol=struct.unpack('<12740f',(out/previous['name']/'color.f32').read_bytes());ccol=struct.unpack('<12740f',(out/current['name']/'color.f32').read_bytes())
   for y in range(49):
    for x in range(65):
     i=y*65+x;actual_delta=(ccol[4*i+3]-pcol[4*i+3])/.375;expected_delta=float(ref.area(current,x,y)-ref.area(previous,x,y));worst=max(worst,abs(actual_delta-expected_delta))
  sequence.append({'group':block[0]['name'].rsplit('-',1)[0],'measured_phase_transitions':3,'max_coverage_delta_error':worst,'qualification':'diagnostic, no additional temporal gate'})
 negative=[]
 for name,hard,double in [('hard-center',True,False),('double-alpha',False,True)]:
  c=CASES[8];draw(name,c,hard,double);r=verify(out/name,c,ref)
  if r['max_composition_depth_error']<=TOL:raise ValueError('negative invisible')
  if hard and r['max_alpha_inferred_coverage_error']<=TOL:raise ValueError('hard-center negative did not change coverage')
  if double and r['max_alpha_inferred_coverage_error']>TOL:raise ValueError('double-alpha negative unexpectedly changed coverage')
  negative.append(dict(mode=name,**r))
 summary=dict(status='BOUNDED_EXACT_RECTANGLE_AREA_PASS',validation_enabled=True,composition_tolerance=TOL,preregistered_area_tolerance=TOL,cases=rows,phase_sequences=sequence,actual_gpu_negatives=negative,limits=['single straight butt/square strokes only','exact rational rectangle area reference, not sampled approximation','not round/joins/curves/general AA/MSAA','alpha-inferred coverage after real blend, not direct separate coverage readback','configured software Vulkan not target device or Live'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [HERE/'reference.py',HERE/'run_lab.py',HERE/'coverage.frag']},generated_main_sha=hashlib.sha256(source.encode()).hexdigest(),binary_sha=hashlib.sha256((out/'area').read_bytes()).hexdigest(),shader_sha={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*-shaders/*.spv')},prepared=json.loads((out/'prepared/local-provenance.json').read_text())),indent=2))
 png=load(HERE.parent/'text_vector_lab/run_lab.py','png').png
 for c in CASES:
  v=struct.unpack('<12740f',(out/c['name']/'color.f32').read_bytes());png(out/c['name']/'preview.png',65,49,bytes(round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)) for i,x in enumerate(v) if i%4!=3))
 print(json.dumps(summary))
if __name__=='__main__':main()
