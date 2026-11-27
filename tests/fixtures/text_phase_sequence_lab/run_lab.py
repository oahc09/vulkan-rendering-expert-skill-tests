#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('switch',HERE.parent/'text_representation_switch_lab/run_lab.py');previous=importlib.util.module_from_spec(s);s.loader.exec_module(previous);q=previous.q;m=q.m
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
SCALE=f32(1.05);PHASES=[f32(i/16) for i in range(17)];BITMAP_TOL=1e-6;MSDF_TOL=.004

def reference(contours,scale,phase):
 m.check_bounds(contours,scale,phase)
 polys=[[((e[0][0]-m.W/2)*scale+m.W/2+phase,(e[0][1]-m.H/2)*scale+m.H/2) for e in c] for c in contours]
 ref=[q.exact(polys,x,y) for y in range(m.H) for x in range(m.W)]
 if any(v< -1e-9 or v>1+1e-9 for v in ref):raise ValueError('area out of range')
 return [min(1,max(0,v)) for v in ref]
def stats(actual,ref):
 diff=[abs(x-y) for x,y in zip(actual,ref)];roi=[i for i,(x,y) in enumerate(zip(actual,ref)) if max(x,y)>1e-5];edge=[i for i in roi if 0<ref[i]<1 or 1e-5<actual[i]<1-1e-5]
 if not roi or not edge:raise ValueError('empty glyph/edge ROI')
 worst=max(roi,key=lambda i:diff[i])
 return dict(max=max(diff[i] for i in roi),foreground_mae=sum(diff[i] for i in roi)/len(roi),edge_mae=sum(diff[i] for i in edge)/len(edge),foreground_pixels=len(roi),edge_pixels=len(edge),worst_xy=[worst%m.W,worst//m.W],worst_actual=actual[worst],worst_reference=ref[worst])
def trace():
 rows=[]
 for b in range(2):
  rows.append(dict(kind='warmup',branch=b,selected=b))
  rows.extend(dict(kind='measured',branch=b,frame=i,previous=b,selected=b) for i in range(17))
 rows.append(dict(kind='negative',branch=0,frame=8,expected=0,actual=1));return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--msdf-source',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 conditions=dict(bitmap_sampling='integer target-pixel texelFetch; exact-area bitmap not platform hinted',msdf_sampling='canonical distance atlas linear4',scale_float32=SCALE,phases_float32=PHASES,origin=[m.W/2,m.H/2],prime_scales_float32=[f32(.85),f32(1.15)],bitmap_threshold=.9,msdf_threshold=1.1,hold='retain previous state',negative_branch=0,negative_phase_index=8,bitmap_rgba_tolerance=BITMAP_TOL,msdf_rgba_tolerance=MSDF_TOL,quality_threshold='none; measurement only',measured_draws=34,warmup_draws=2,negative_draws=1)
 (out/'conditions.json').write_text(json.dumps(conditions,indent=2))
 prep=out/'preparation'
 with (out/'prepare.log').open('w') as log:subprocess.run([sys.executable,str(HERE.parent/'text_representation_switch_lab/run_lab.py'),'--out',str(prep),'--font',str(a.font),'--msdf-source',str(a.msdf_source)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=360)
 contours=json.loads((prep/'baseline/A/outline.json').read_text())
 if any(len(e)!=2 for c in contours for e in c):raise ValueError('linear glyph only')
 refs=[reference(contours,SCALE,phase) for phase in PHASES];warmrefs=[reference(contours,scale,0) for scale in conditions['prime_scales_float32']]
 inputs=out/'inputs';inputs.mkdir();shutil.copyfile(prep/'inputs/msdf.rgba32f',inputs/'msdf.rgba32f')
 for name,ref in [(str(i),ref) for i,ref in enumerate(refs)]+[('warm'+str(i),ref) for i,ref in enumerate(warmrefs)]:
  values=[v for c in ref for v in (c,c,c,1.)];(inputs/(name+'.rgba32f')).write_bytes(struct.pack('<'+str(len(values))+'f',*values))
 shutil.copyfile(prep/'switch_helper.hpp',out/'switch_helper.hpp');shutil.copytree(prep/'shaders',out/'shaders')
 subprocess.run([os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',str(HERE/'bitmap.frag'),'-o',str(out/'shaders/bitmap.frag.spv')],check=True,timeout=30)
 subprocess.run([os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',str(out/'shaders/bitmap.frag.spv')],check=True,timeout=30)
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(out),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',str(HERE/'main.cpp'),'-l:libvulkan.so.1','-o',str(out/'phase_lab')],check=True,timeout=180)
 r=subprocess.run([str(out/'phase_lab'),str(out/'shaders'),str(inputs),str(out/'frames')],capture_output=True,text=True,timeout=120);(out/'run.log').write_text(r.stdout+r.stderr)
 if r.returncode or 'VALIDATION:' in r.stderr or 'validation_enabled=1' not in r.stdout:raise ValueError('GPU execution/validation')
 events=[json.loads(line) for line in (out/'frames/events.jsonl').read_text().splitlines()]
 if events!=trace():raise ValueError('route trace mismatch')
 atlas=m.floats(inputs/'msdf.rgba32f',m.W*m.H*4);frames=[[],[]];rows=[];warmrows=[];preview=m.load(HERE.parent/'text_vector_lab/run_lab.py','phase_preview')
 def verify(folder,mode,scale,phase,ref):
  rgba=m.floats(folder/'color.rgba32f',m.W*m.H*4);expected=q.sampled(atlas,scale,phase,'linear4') if mode else ref;err=previous.error(rgba,expected)
  if err>(MSDF_TOL if mode else BITMAP_TOL):raise ValueError('sampling/composition mismatch')
  for filename,sentinel in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
   if any(v!=sentinel[i%4] for i,v in enumerate(m.floats(folder/(filename+'.rgba32f'),m.W*m.H*4))):raise ValueError('sentinel mismatch')
  def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
  preview.png(folder/'preview.png',m.W,m.H,bytes(enc(rgba[i*4+c]) for i in range(m.W*m.H) for c in range(3)))
  actual=[(rgba[i*4+3]-.5)/.375 for i in range(m.W*m.H)];return actual,dict(sampling_rgba_error=err,exact_area_error=stats(actual,ref))
 for branch in range(2):
  _,wr=verify(out/'frames'/('warm'+str(branch)),branch,conditions['prime_scales_float32'][branch],0,warmrefs[branch]);wr['branch']=branch;warmrows.append(wr)
  for i,phase in enumerate(PHASES):
   actual,row=verify(out/'frames'/(str(branch)+'-'+str(i)),branch,SCALE,phase,refs[i]);frames[branch].append(actual);row.update(branch=branch,phase_index=i,phase=phase);rows.append(row)
 bad=m.floats(out/'frames/wrong-hold/color.rgba32f',m.W*m.H*4);negative=previous.error(bad,refs[8])
 if negative<=BITMAP_TOL or events[-1]['actual']==events[-1]['expected']:raise ValueError('wrong route/image not rejected')
 paired=[dict(phase_index=i,phase=PHASES[i],difference=stats(frames[1][i],frames[0][i])) for i in range(17)]
 temporal=[]
 for branch in range(2):
  for i in range(1,17):
   actual=frames[branch][i];prior=frames[branch][i-1];res=[(actual[j]-prior[j])-(refs[i][j]-refs[i-1][j]) for j in range(m.W*m.H)];roi=[j for j in range(m.W*m.H) if max(actual[j],prior[j],refs[i][j],refs[i-1][j])>1e-5];edge=[j for j in roi if 0<refs[i][j]<1 or 0<refs[i-1][j]<1];worst=max(roi,key=lambda j:abs(res[j]))
   temporal.append(dict(branch=branch,from_phase=PHASES[i-1],to_phase=PHASES[i],max=abs(res[worst]),foreground_mae=sum(abs(res[j]) for j in roi)/len(roi),edge_mae=sum(abs(res[j]) for j in edge)/len(edge),worst_xy=[worst%m.W,worst//m.W],worst_signed_residual=res[worst]))
 summary=dict(status='MEASURED_NOT_QUALIFIED',conditions=conditions,warmup=warmrows,frames=rows,same_phase_representation_difference=paired,temporal_geometry_subtracted_residual=temporal,negative_wrong_hold_rgba_error=negative,scope='same glyph normalized outline/origin and float32 transform; one VkDevice two persistent representation pipelines; fixed-camera horizontal phase only',limits=['bitmap exact-area generation and reference are same producer: only transport/composition proven','MSDF exact-polygon reference independent of its distance field','temporal metric is same-pixel diagnostic not perceptual flicker or motion-compensated acceptance','no platform hinted quality, rotation, perspective, device/performance acceptance'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps(dict(preparation_receipt='preparation/local-provenance.json',sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'main.cpp',HERE/'bitmap.frag',HERE/'run_lab.py']},binary_sha256=hashlib.sha256((out/'phase_lab').read_bytes()).hexdigest()),indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
