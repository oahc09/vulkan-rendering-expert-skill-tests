#!/usr/bin/env python3
"""Actual trusted-font outline -> pinned msdfgen core -> Vulkan linear RGB MSDF.

CPU median/bilinear oracle checks sampling/composition; independent subdivided
outline supersampling checks coverage. Neither is target-device font certification.
No network or font/source redistribution. Dependency must already be local.
"""
import argparse,bisect,hashlib,importlib.util,json,math,os,struct,subprocess,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
FONT_SHA256='57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e'
MSDF_COMMIT='1874bcf7d9624ccc85b4bc9a85d78116f690f35b'
# Pre-registered BEFORE the first run. Do not tune after observing failures.
CASES=[('small',.75,0.),('native',1.,0.),('large',1.5,0.),('phase',1.,.25)]
SAMPLE_TOLERANCE=2e-4
ROI_MAE_LIMIT=.04
EDGE_MAE_LIMIT=.16
MAX_COVERAGE_ERROR=.45
SUPERSAMPLES=16
CURVE_STEPS=64

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def outlines(font,letter):
 import freetype
 provider=load(ROOT/'tests/platform_text_probe.py','msdf_provider')
 run=provider.shape(font,letter,language='en')
 if run['missing_glyphs'] or len(run['glyphs'])!=1:raise ValueError('one supported shaped glyph required')
 face=freetype.Face(str(font));face.load_glyph(run['glyphs'][0]['id'],freetype.FT_LOAD_NO_SCALE|freetype.FT_LOAD_NO_HINTING|freetype.FT_LOAD_NO_BITMAP)
 if face.glyph.format!=freetype.FT_GLYPH_FORMAT_OUTLINE:raise ValueError('outline unavailable')
 contours=[];current=[];point=None;start=None
 def xy(p):return (float(p.x),-float(p.y))
 def close():
  nonlocal current,point,start
  if current:
   if point!=start:current.append([point,start])
   contours.append(current)
  current=[]
 def move(p,ctx):
  nonlocal point,start
  close();point=start=xy(p)
 def line(p,ctx):
  nonlocal point
  end=xy(p);current.append([point,end]);point=end
 def conic(c,p,ctx):
  nonlocal point
  end=xy(p);current.append([point,xy(c),end]);point=end
 def cubic(c1,c2,p,ctx):
  nonlocal point
  end=xy(p);current.append([point,xy(c1),xy(c2),end]);point=end
 face.glyph.outline.decompose(move_to=move,line_to=line,conic_to=conic,cubic_to=cubic);close()
 points=[p for c in contours for e in c for p in e]
 if not points or len(points)>16384:raise ValueError('outline budget')
 xmin=min(x for x,y in points);xmax=max(x for x,y in points);ymin=min(y for x,y in points);ymax=max(y for x,y in points)
 if ymax<=ymin:raise ValueError('degenerate glyph')
 scale=24/(ymax-ymin);cx=(xmin+xmax)/2;cy=(ymin+ymax)/2
 contours=[[[((x-cx)*scale+W/2,(y-cy)*scale+H/2) for x,y in e] for e in c] for c in contours]
 run.update(outline_provider='FreeType FT_LOAD_NO_SCALE|NO_HINTING|NO_BITMAP',freetype_version=list(freetype.version()),freetype_library_sha256=sha(Path(freetype.raw._lib._name)),outline_height=24,curve_subdivision_steps=CURVE_STEPS)
 return contours,run

def check_bounds(contours,scale=1.,phase=0.,margin=0.):
 # Bezier curves lie inside their control-point convex hull; reject clipping.
 points=[(W/2+(x-W/2)*scale+phase,H/2+(y-H/2)*scale) for c in contours for e in c for x,y in e]
 if not points or any(not (margin<x<W-margin and margin<y<H-margin) for x,y in points):
  raise ValueError('outline clipping/padding budget')

def flatten(contours):
 edges=[]
 for contour in contours:
  for e in contour:
   if len(e)==2:edges.append((e[0],e[1]));continue
   last=e[0]
   for j in range(1,CURVE_STEPS+1):
    t=j/CURVE_STEPS;u=1-t
    weights=(u*u,2*u*t,t*t) if len(e)==3 else (u**3,3*u*u*t,3*u*t*t,t**3)
    p=tuple(sum(a[k]*w for a,w in zip(e,weights)) for k in (0,1))
    edges.append((last,p));last=p
 return edges

def geometry_coverage(contours,scale,phase):
 # Independent even-odd scanline coverage of the source outline, not MSDF pixels.
 edges=[(((a[0]-W/2)*scale+W/2+phase,(a[1]-H/2)*scale+H/2),((b[0]-W/2)*scale+W/2+phase,(b[1]-H/2)*scale+H/2)) for a,b in flatten(contours)]
 result=[0.]*(W*H)
 for y in range(H):
  for sy in range(SUPERSAMPLES):
   yy=y+(sy+.5)/SUPERSAMPLES;xs=[]
   for (ax,ay),(bx,by) in edges:
    if (ay<=yy<by) or (by<=yy<ay):xs.append(ax+(yy-ay)*(bx-ax)/(by-ay))
   xs.sort()
   if len(xs)%2:raise ValueError('unclosed independent outline')
   for x in range(W):
    count=sum(bisect.bisect_right(xs,x+(sx+.5)/SUPERSAMPLES)%2 for sx in range(SUPERSAMPLES))
    result[y*W+x]+=count/(SUPERSAMPLES**2)
 return result

def bilinear(atlas,x,y):
 # Vulkan normalized LINEAR coordinates mapped to texel-center space.
 x-=.5;y-=.5;ix=math.floor(x);iy=math.floor(y);fx=x-ix;fy=y-iy
 def p(a,b,c):return atlas[(min(H-1,max(0,b))*W+min(W-1,max(0,a)))*4+c]
 return [p(ix,iy,c)*(1-fx)*(1-fy)+p(ix+1,iy,c)*fx*(1-fy)+p(ix,iy+1,c)*(1-fx)*fy+p(ix+1,iy+1,c)*fx*fy for c in range(3)]

def reconstructed(atlas,scale,phase):
 result=[]
 for y in range(H):
  for x in range(W):
   rgb=bilinear(atlas,(x+.5-W/2-phase)/scale+W/2,(y+.5-H/2)/scale+H/2)
   result.append(min(1.,max(0.,(sorted(rgb)[1]-.5)*max(4*scale,1)+.5)))
 return result

def floats(path,n):
 b=path.read_bytes()
 if len(b)!=n*4:raise ValueError('readback size')
 a=struct.unpack('<'+'f'*n,b)
 if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite data')
 return a

def verify_case(folder,atlas,contours,scale,phase):
 rgba=floats(folder/'color.rgba32f',W*H*4);expected=reconstructed(atlas,scale,phase);actual=[];errors=[]
 for i,cov in enumerate(expected):
  a=cov*.75;actual.append((rgba[i*4+3]-.5)/.375)
  for c in range(4):errors.append(abs(rgba[4*i+c]-((a if c==3 else (.9,.5,.2)[c]*a)+(.1,.2,.3,.5)[c]*(1-a))))
 if max(errors)>SAMPLE_TOLERANCE:raise ValueError('MSDF sampling/composition mismatch')
 for file,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(v!=values[i%4] for i,v in enumerate(floats(folder/(file+'.rgba32f'),W*H*4))):raise ValueError('non-target attachment modified')
 geo=geometry_coverage(contours,scale,phase);diff=[abs(a-b) for a,b in zip(actual,geo)]
 roi=[i for i,(a,b) in enumerate(zip(actual,geo)) if a>1e-5 or b>0]
 edge=[i for i in roi if 0<geo[i]<1 or 1e-5<actual[i]<1-1e-5]
 if not roi or not edge:raise ValueError('empty quality ROI')
 roi_mae=sum(diff[i] for i in roi)/len(roi);edge_mae=sum(diff[i] for i in edge)/len(edge)
 metrics=dict(sample_error=max(errors),roi_mae=roi_mae,edge_mae=edge_mae,max_coverage_error=max(diff),roi_pixels=len(roi),edge_pixels=len(edge))
 (folder/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','msdf_preview')
 def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
 preview.png(folder/'preview.png',W,H,bytes(enc(rgba[4*i+c]) for i in range(W*H) for c in range(3)))
 preview.png(folder/'outline-reference.png',W,H,bytes(round(255*v) for v in geo for c in range(3)))
 if roi_mae>ROI_MAE_LIMIT or edge_mae>EDGE_MAE_LIMIT or max(diff)>MAX_COVERAGE_ERROR:raise ValueError('independent outline coverage gate failed')
 return metrics

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--font',required=True,type=Path);p.add_argument('--msdf-source',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 (out/'preregistered.json').write_text(json.dumps(dict(cases=CASES,px_range=4,source=MSDF_COMMIT,sample_tolerance=SAMPLE_TOLERANCE,roi_mae=ROI_MAE_LIMIT,edge_mae=EDGE_MAE_LIMIT,max_coverage_error=MAX_COVERAGE_ERROR,supersamples=SUPERSAMPLES,curve_steps=CURVE_STEPS),indent=2)+'\n')
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed: '+log[-2000:])
  return log
 if not a.font.is_file() or a.font.is_symlink() or a.font.stat().st_size>16*1024*1024 or sha(a.font)!=FONT_SHA256:raise ValueError('unapproved font bytes; trusted fixture only')
 source=a.msdf_source.resolve()
 if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=30).strip()!=MSDF_COMMIT:raise ValueError('unpinned msdf source')
 if subprocess.check_output(['git','-C',str(source),'status','--porcelain','--untracked-files=all'],text=True,timeout=30).strip():raise ValueError('dirty msdf source')
 flags=subprocess.check_output(['git','-C',str(source),'ls-files','-v','-z'],timeout=30).split(b'\0')
 if any(record and (record[:1].islower() or record[:1]==b'S') for record in flags):raise ValueError('hidden dependency index flags')
 # Compare required compiled files directly to immutable git blob bytes as well.
 dependency_files=[source/'LICENSE.txt',source/'msdfgen.h',*sorted((source/'core').glob('*'))]
 for path in dependency_files:
  if not path.is_file():continue
  if path.is_symlink():raise ValueError('dependency symlink')
  committed=subprocess.check_output(['git','-C',str(source),'show',MSDF_COMMIT+':'+str(path.relative_to(source))],timeout=30)
  if path.read_bytes()!=committed:raise ValueError('dependency blob mismatch')
 base=HERE.parent/'text_vector_lab';build=out/'build';run('base-build',[base/'build.sh',build])
 run('msdf-build',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-DMSDFGEN_PUBLIC=','-DMSDFGEN_USE_CPP11','-I'+str(source),HERE/'generate.cpp',*sorted((source/'core').glob('*.cpp')),'-o',build/'generate'])
 def replace(text,old,new,count=1):
  if text.count(old)!=count:raise ValueError('reused source hook changed: '+old)
  return text.replace(old,new)
 cpp=(base/'main.cpp').read_text();cpp=replace(cpp,'int main(int argc,char** argv)','int old_msdf_main(int argc,char** argv)');cpp=replace(cpp,'../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'))
 cpp=replace(cpp,'struct TextLab: Vulkan {','struct TextLab: Vulkan {\n float msdfScale=1,msdfPhase=0,msdfRange=4;')
 cpp=replace(cpp,'VK_FORMAT_R32_SFLOAT','VK_FORMAT_R32G32B32A32_SFLOAT',2)
 cpp=replace(cpp,'VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT','VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT')
 cpp=replace(cpp,'auto usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT', '''vkDestroySampler(device,sampler,nullptr);sampler=VK_NULL_HANDLE;
    VkSamplerCreateInfo sci{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};sci.magFilter=sci.minFilter=VK_FILTER_LINEAR;sci.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;sci.addressModeU=sci.addressModeV=sci.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;sci.maxLod=0;VK(vkCreateSampler(device,&sci,nullptr,&sampler));
    auto usage=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT''')
 cpp=replace(cpp,'buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)','buffer(width*height*16,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)')
 cpp=replace(cpp,'VK_SHADER_STAGE_FRAGMENT_BIT,0,16','VK_SHADER_STAGE_FRAGMENT_BIT,0,32',2)
 cpp=replace(cpp,'mask.size()!=width*height','mask.size()!=width*height*4')
 cpp=replace(cpp,'float rgba[]={ink[0],ink[1],ink[2],ink[3]};','float rgba[]={ink[0],ink[1],ink[2],ink[3],msdfScale,msdfPhase,msdfRange,0};')
 (build/'msdf_lab_reused.hpp').write_text(cpp)
 command=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
 if os.environ.get('VULKAN_SDK_PREFIX'):command+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('vulkan-build',command+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'msdf_lab'])
 variants={}
 for name,define in [('correct',None),('wrong-channel','WRONG_CHANNEL'),('wrong-srgb','WRONG_SRGB')]:
  folder=build/name;folder.mkdir()
  for shader in (build/'shaders').glob('*.spv'):(folder/shader.name).write_bytes(shader.read_bytes())
  args=[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2']
  if define:args+=['-D'+define+'=1']
  run('compile-'+name,args+[HERE/'msdf.frag','-o',folder/'coverage.frag.spv']);run('validate-'+name,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',folder/'coverage.frag.spv']);variants[name]=folder
 rows=[];negative=[]
 for letter in ['A','O']:
  folder=out/letter;folder.mkdir();contours,receipt=outlines(a.font,letter)
  check_bounds(contours,margin=3.) # Half distance range (2) plus linear footprint (1).
  (folder/'provider.json').write_text(json.dumps(receipt,indent=2)+'\n');(folder/'outline.json').write_text(json.dumps(contours)+'\n')
  lines=[str(len(contours))]
  for c in contours:
   lines.append(str(len(c)))
   for e in c:lines.append(str(len(e))+' '+' '.join(str(v) for point in e for v in point))
  (folder/'outline.txt').write_text('\n'.join(lines)+'\n')
  run('generate-'+letter,[build/'generate',folder/'outline.txt',folder/'atlas.rgba32f'])
  atlas=floats(folder/'atlas.rgba32f',W*H*4)
  if letter=='A' and not any(abs(atlas[i]-atlas[i+1])>1e-4 for i in range(0,len(atlas),4)):raise ValueError('expected independently colored distance channels')
  for case,scale,phase in CASES:
   check_bounds(contours,scale,phase)
   log=run(letter+'-'+case,[build/'msdf_lab',variants['correct'],folder/'atlas.rgba32f',scale,phase,4,folder/case])
   if 'validation_enabled=1' not in log:raise ValueError('validation required')
   metrics=verify_case(folder/case,atlas,contours,scale,phase);metrics.update(glyph=letter,case=case);rows.append(metrics)
  if letter=='A':
   for name,shader,rng in [('wrong-channel','wrong-channel',4),('wrong-srgb','wrong-srgb',4),('wrong-range','correct',1)]:
    run(name,[build/'msdf_lab',variants[shader],folder/'atlas.rgba32f',1,0,rng,folder/name])
    try:verify_case(folder/name,atlas,contours,1,0)
    except ValueError as e:
     if 'sampling/composition' not in str(e):raise
     negative.append(name)
    else:raise ValueError('negative shader/range accepted')
 provenance={'msdf_commit':MSDF_COMMIT,'msdf_source_files':{str(p.relative_to(source)):sha(p) for p in [source/'LICENSE.txt',source/'msdfgen.h',*sorted((source/'core').glob('*'))] if p.is_file()},'fixture_sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'generate.cpp',HERE/'main.cpp',HERE/'msdf.frag',HERE/'run_lab.py',base/'main.cpp',HERE.parent/'engine_scale_lab/main.cpp',ROOT/'tests/platform_text_probe.py']},'font_sha256':sha(a.font),'generator_binary_sha256':sha(build/'generate'),'vulkan_binary_sha256':sha(build/'msdf_lab')}
 tool_receipts={}
 for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
  path=Path(shutil.which(os.environ.get(key,default)) or os.environ.get(key,default)).resolve()
  tool_receipts[key]={'path':str(path),'sha256':sha(path),'version':subprocess.check_output([str(path),'--version'],text=True,timeout=15).strip()}
 runtime_files={}
 manifests=[Path(p) for p in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep) if p]
 manifests += [p for d in os.environ.get('VK_LAYER_PATH','').split(os.pathsep) if d for p in Path(d).glob('*validation*.json')]
 for manifest in manifests:
  runtime_files[str(manifest)]=sha(manifest)
  document=json.loads(manifest.read_text());entry=document.get('ICD',document.get('layer',{}));name=entry.get('library_path')
  if not name:raise ValueError('runtime manifest lacks library')
  candidates=[Path(name)] if Path(name).is_absolute() else [manifest.parent/name,*[Path(d)/name for d in os.environ.get('LD_LIBRARY_PATH','').split(os.pathsep) if d]]
  library=next((p.resolve() for p in candidates if p.is_file()),None)
  if library is None:raise ValueError('runtime library provenance missing')
  runtime_files[str(library)]=sha(library)
 provenance.update(tools=tool_receipts,runtime_files=runtime_files,python=sys.version)
 (out/'local-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 summary={'status':'PASS','cases':rows,'negatives':negative,'scope':'Linux trusted-font A/O outlines; official edge-colored MSDF; linear RGB software Vulkan; independent outline coverage at registered transforms','not_claimed':['MTSDF','paragraph/fallback','arbitrary perspective','optimal small-font quality','Android/Windows provider','hardware/performance'],'third_party_source_bundled':False}
 summary.update(acceptance='bounded experimental not full quality',limits={'sample_tolerance':SAMPLE_TOLERANCE,'roi_mae':ROI_MAE_LIMIT,'edge_mae':EDGE_MAE_LIMIT,'max_coverage_error':MAX_COVERAGE_ERROR},max_observed_coverage_error=max(row['max_coverage_error'] for row in rows),mrt_scope='UNUSED/preserve fallback, not active MRT')
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
