#!/usr/bin/env python3
"""Actual GPU higher-grid phase experiment; no product quality qualification."""
import argparse,hashlib,importlib.util,json,math,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'text_phase_sequence_lab/run_lab.py'
s=importlib.util.spec_from_file_location('phase_base',BASE);b=importlib.util.module_from_spec(s);s.loader.exec_module(b);m=b.m

def sampled(atlas,scale,phase,n):
 if n not in (4,8,16):raise ValueError('grid')
 result=[]
 for y in range(m.H):
  for x in range(m.W):
   ax0=(x-m.W/2-phase)/scale+m.W/2-.5;ax1=(x+1-m.W/2-phase)/scale+m.W/2-.5
   ay0=(y-m.H/2)/scale+m.H/2-.5;ay1=(y+1-m.H/2)/scale+m.H/2-.5
   v=[atlas[(min(m.H-1,max(0,yy))*m.W+min(m.W-1,max(0,xx)))*4+c] for yy in range(math.floor(ay0),math.floor(ay1)+2) for xx in range(math.floor(ax0),math.floor(ax1)+2) for c in range(3)]
   pad=.5/(4*scale*n)
   if min(v)>.5+pad:result.append(1.);continue
   if max(v)<.5-pad:result.append(0.);continue
   total=0.
   for sy in range(n):
    for sx in range(n):
     ax=(x+(sx+.5)/n-m.W/2-phase)/scale+m.W/2;ay=(y+(sy+.5)/n-m.H/2)/scale+m.H/2
     sd=sorted(m.bilinear(atlas,ax,ay))[1]-.5
     total+=min(1,max(0,sd*4*scale*n+.5))
   result.append(total/(n*n))
 return result

def temporal(frames,refs):
 rows=[]
 for branch in range(2):
  for i in range(1,17):
   cur,prev=frames[branch][i],frames[branch][i-1]
   r=[(cur[j]-prev[j])-(refs[i][j]-refs[i-1][j]) for j in range(m.W*m.H)]
   roi=[j for j in range(m.W*m.H) if max(cur[j],prev[j],refs[i][j],refs[i-1][j])>1e-5]
   edge=[j for j in roi if 0<refs[i][j]<1 or 0<refs[i-1][j]<1];w=max(roi,key=lambda j:abs(r[j]))
   rows.append(dict(branch=branch,from_phase=b.PHASES[i-1],to_phase=b.PHASES[i],max=abs(r[w]),foreground_mae=sum(abs(r[j]) for j in roi)/len(roi),edge_mae=sum(abs(r[j]) for j in edge)/len(edge),worst_xy=[w%m.W,w//m.W],worst_signed_residual=r[w]))
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--msdf-source',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 conditions=dict(grids=[4,8,16],samples_per_pixel=[16,64,256],phases=b.PHASES,scale_float32=b.SCALE,bitmap_rgba_tolerance=b.BITMAP_TOL,msdf_rgba_tolerance=b.MSDF_TOL,quality_threshold='none; no required improvement; original gates unchanged',measured_per_mode=34,warmup_per_mode=2,negative_per_mode=1,scope='same original A atlas and history schedule; mode processes use separate devices, each contains both representations')
 (out/'conditions.json').write_text(json.dumps(conditions,indent=2))
 def run(name,args,timeout=120):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed')
  return log
 base=out/'linear4';run('baseline',[sys.executable,BASE,'--out',base,'--font',a.font,'--msdf-source',a.msdf_source],360)
 original=json.loads((base/'summary.json').read_text());modes={'linear4':original}
 contours=json.loads((base/'preparation/baseline/A/outline.json').read_text());refs=[b.reference(contours,b.SCALE,phase) for phase in b.PHASES]
 atlas=m.floats(base/'inputs/msdf.rgba32f',m.W*m.H*4)
 preview=m.load(HERE.parent/'text_vector_lab/run_lab.py','integration_preview')
 for n in (8,16):
  folder=out/('linear'+str(n));folder.mkdir();shutil.copytree(base/'shaders',folder/'shaders')
  run('compile-'+str(n),[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2','-DGRID='+str(n),HERE/'integrate.frag','-o',folder/'shaders/coverage.frag.spv'])
  run('spirv-'+str(n),[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',folder/'shaders/coverage.frag.spv'])
  log=run('gpu-'+str(n),[base/'phase_lab',folder/'shaders',base/'inputs',folder/'frames'])
  events=[json.loads(x) for x in (folder/'frames/events.jsonl').read_text().splitlines()]
  if 'validation_enabled=1' not in log or events!=b.trace():raise ValueError('trace/validation')
  frames=[[],[]];rows=[];warm=[]
  def verify(path,branch,scale,phase,ref):
   rgba=m.floats(path/'color.rgba32f',m.W*m.H*4);expected=sampled(atlas,scale,phase,n) if branch else ref;err=b.previous.error(rgba,expected)
   if err>(b.MSDF_TOL if branch else b.BITMAP_TOL):raise ValueError('sampling/composition mismatch')
   for name,t in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
    if any(v!=t[i%4] for i,v in enumerate(m.floats(path/(name+'.rgba32f'),m.W*m.H*4))):raise ValueError('sentinel mismatch')
   actual=[(rgba[i*4+3]-.5)/.375 for i in range(m.W*m.H)]
   def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
   preview.png(path/'preview.png',m.W,m.H,bytes(enc(rgba[i*4+c]) for i in range(m.W*m.H) for c in range(3)))
   return actual,dict(sampling_rgba_error=err,exact_area_error=b.stats(actual,ref))
  for branch in range(2):
   scale=b.f32(1.15 if branch else .85);_,row=verify(folder/'frames'/('warm'+str(branch)),branch,scale,0,b.reference(contours,scale,0));row['branch']=branch;warm.append(row)
   for i,phase in enumerate(b.PHASES):
    actual,row=verify(folder/'frames'/(str(branch)+'-'+str(i)),branch,b.SCALE,phase,refs[i]);frames[branch].append(actual);row.update(branch=branch,phase_index=i,phase=phase);rows.append(row)
  # Wrong route is a valid opposite representation; check every channel and auxiliaries too.
  verify(folder/'frames/wrong-hold',1,b.SCALE,b.PHASES[8],refs[8])
  bad=m.floats(folder/'frames/wrong-hold/color.rgba32f',m.W*m.H*4);negative=b.previous.error(bad,refs[8])
  if negative<=b.BITMAP_TOL:raise ValueError('negative not detected')
  modes['linear'+str(n)]=dict(frames=rows,warmup=warm,temporal_geometry_subtracted_residual=temporal(frames,refs),negative_wrong_hold_rgba_error=negative)
 summary=dict(status='MEASURED_NOT_QUALIFIED',conditions=conditions,modes=modes,limits=['bitmap reference same producer: transport only','actual GPU linear8/16 versus actual linear4, fixed A phase sweep only','higher samples not proven faster or mobile feasible; timestamp and thermal cost unmeasured','not rotation/perspective, perceptual flicker, full quality or generator defect proof'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
 hashes=lambda ps:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ps}
 (out/'local-provenance.json').write_text(json.dumps(dict(sources=hashes([HERE/'run_lab.py',HERE/'integrate.frag',BASE,BASE.parent/'main.cpp']),inputs=hashes([base/'inputs/msdf.rgba32f',base/'phase_lab']),generated_shaders=hashes([out/'linear8/shaders/coverage.frag.spv',out/'linear16/shaders/coverage.frag.spv']),preparation_receipt='linear4/local-provenance.json'),indent=2))
 print(json.dumps({mode:{'exact_max':max(r['exact_area_error']['max'] for r in data['frames'] if r['branch']==1),'temporal_max':max(r['max'] for r in data['temporal_geometry_subtracted_residual'] if r['branch']==1)} for mode,data in modes.items()}))
if __name__=='__main__':main()
