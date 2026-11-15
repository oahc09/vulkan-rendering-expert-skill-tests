#!/usr/bin/env python3
"""Bounded 256-sample MSDF experiment, not a production quality/performance pass."""
import argparse,importlib.util,json,os,subprocess,sys,shutil,hashlib,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'text_msdf_lab/run_lab.py'
s=importlib.util.spec_from_file_location('msdf_base',BASE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def clip(poly,axis,limit,greater):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ai=(a[axis]>=limit if greater else a[axis]<=limit);bi=(b[axis]>=limit if greater else b[axis]<=limit)
  if ai:out.append(a)
  if ai!=bi:
   t=(limit-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[k]+t*(b[k]-a[k]) for k in (0,1)))
 return out
def area(poly):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))*.5
def exact(polys,x,y):
 total=0
 for p in polys:
  for axis,lim,g in [(0,x,1),(0,x+1,0),(1,y,1),(1,y+1,0)]:p=clip(p,axis,lim,g)
  total+=area(p)
 return abs(total)
def sampled(atlas,scale,phase,mode):
 n=16 if mode=="binary16" else 4
 result=[]
 for y in range(m.H):
  for x in range(m.W):
   # Convex bilinear samples cannot cross zero if every contributing RGB
   # texel has the same strict sign; exact safe shortcut, not an ROI crop.
   ax0=(x-m.W/2-phase)/scale+m.W/2-.5;ax1=(x+1-m.W/2-phase)/scale+m.W/2-.5
   ay0=(y-m.H/2)/scale+m.H/2-.5;ay1=(y+1-m.H/2)/scale+m.H/2-.5
   values=[atlas[(min(m.H-1,max(0,yy))*m.W+min(m.W-1,max(0,xx)))*4+c] for yy in range(math.floor(ay0),math.floor(ay1)+2) for xx in range(math.floor(ax0),math.floor(ax1)+2) for c in range(3)]
   pad=0 if mode=='binary16' else .5/(4*scale*n)
   if min(values)>.5+pad:result.append(1.);continue
   if max(values)<.5-pad:result.append(0.);continue
   total=0
   for sy in range(n):
    for sx in range(n):
     ax=(x+(sx+.5)/n-m.W/2-phase)/scale+m.W/2
     ay=(y+(sy+.5)/n-m.H/2)/scale+m.H/2
     sd=sorted(m.bilinear(atlas,ax,ay))[1]-.5
     total+=(sd>=0) if mode=='binary16' else min(1,max(0,sd*4*scale*n+.5))
   result.append(total/(n*n))
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--msdf-source',type=Path,required=True);a=p.parse_args()
 out=a.out.resolve();out.mkdir(exist_ok=False)
 (out/'conditions.json').write_text(json.dumps({'status':'MEASURED_NOT_QUALIFIED','samples_per_pixel':{'binary16':256,'linear4':16},'sampling_oracle_tolerance':.004,'old_quality_limits_unchanged':True,'cases':m.CASES},indent=2))
 root=out/'baseline'
 subprocess.run([sys.executable,str(BASE),'--out',str(root),'--font',str(a.font),'--msdf-source',str(a.msdf_source)],check=True,timeout=360,stdout=(out/'baseline.log').open('w'),stderr=subprocess.STDOUT)
 for mode in ['binary16','linear4']:
  for name in [mode+'-shaders',mode+'-negative-shaders']:
   shutil.copytree(root/'build/correct',out/name)
   command=[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2']
   if 'negative' in name:command+=['-DWRONG_SRGB=1']
   if mode=='linear4':command+=['-DLINEAR4=1']
   subprocess.run(command+[str(HERE/'integrate.frag'),'-o',str(out/name/'coverage.frag.spv')],check=True,timeout=30)
   subprocess.run([os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',str(out/name/'coverage.frag.spv')],check=True,timeout=30)
 rows=[]
 negatives={}
 for mode in ['binary16','linear4']:
  for letter in ['A','O']:
   contours=json.loads((root/letter/'outline.json').read_text())
   for case,scale,phase in m.CASES:
    folder=out/(mode+'-'+letter+'-'+case)
    r=subprocess.run([str(root/'build/msdf_lab'),str(out/(mode+'-shaders')),str(root/letter/'atlas.rgba32f'),str(scale),str(phase),'4',str(folder)],capture_output=True,text=True,check=True,timeout=60)
    (out/(mode+'-'+letter+'-'+case+'.log')).write_text(r.stdout+r.stderr)
    if 'validation_enabled=1' not in r.stdout or 'VALIDATION:' in r.stderr:raise ValueError('validation missing')
    atlas=m.floats(root/letter/'atlas.rgba32f',m.W*m.H*4)
    expected=sampled(atlas,scale,phase,mode)
    rgba=m.floats(folder/'color.rgba32f',m.W*m.H*4);actual=[(rgba[i*4+3]-.5)/.375 for i in range(m.W*m.H)]
    sample_error=max(abs(a-b) for a,b in zip(actual,expected))
    rgba_error=max(abs(rgba[i*4+c]-((a*.75 if c==3 else (.9,.5,.2)[c]*a*.75)+(.1,.2,.3,.5)[c]*(1-a*.75))) for i,a in enumerate(expected) for c in range(4))
    if sample_error>.004 or rgba_error>.004:raise ValueError('subpixel RGBA sampling/composition oracle mismatch')
    ref=m.geometry_coverage(contours,scale,phase);diff=[abs(a-b) for a,b in zip(actual,ref)];roi=[i for i,(a,b) in enumerate(zip(actual,ref)) if a>1e-5 or b>0]
    baseline=json.loads((root/letter/case/'metrics.json').read_text())
    if max(diff)>=baseline['max_coverage_error']:raise ValueError('fixed-case improvement regression')
    row=dict(mode=mode,rgba_error=rgba_error,sample_error=sample_error,glyph=letter,case=case,baseline=baseline,max_error=max(diff),roi_mae=sum(diff[i] for i in roi)/len(roi))
    if letter=='A':
     if any(len(e)!=2 for c in contours for e in c):raise ValueError('exact polygon diagnostic requires linear edges')
     polys=[[((e[0][0]-m.W/2)*scale+m.W/2+phase,(e[0][1]-m.H/2)*scale+m.H/2) for e in c] for c in contours]
     exact_ref=[exact(polys,x,y) for y in range(m.H) for x in range(m.W)]
     row['exact_polygon_max_error']=max(abs(a-b) for a,b in zip(actual,exact_ref))
     baseline_rgba=m.floats(root/letter/case/'color.rgba32f',m.W*m.H*4)
     row['baseline_exact_polygon_max_error']=max(abs((baseline_rgba[4*i+3]-.5)/.375-b) for i,b in enumerate(exact_ref))
    for file,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
     if not all(v==values[i%4] for i,v in enumerate(m.floats(folder/(file+'.rgba32f'),m.W*m.H*4))):raise ValueError('UNUSED attachment modified')
    rows.append(row)
  folder=out/(mode+'-negative-srgb')
  r=subprocess.run([str(root/'build/msdf_lab'),str(out/(mode+'-negative-shaders')),str(root/'A/atlas.rgba32f'),'1','0','4',str(folder)],capture_output=True,text=True,check=True,timeout=60)
  (out/(mode+'-negative-srgb.log')).write_text(r.stdout+r.stderr)
  if 'validation_enabled=1' not in r.stdout or 'VALIDATION:' in r.stderr:raise ValueError('negative validation missing')
  rgba=m.floats(folder/'color.rgba32f',m.W*m.H*4);actual=[(rgba[i*4+3]-.5)/.375 for i in range(m.W*m.H)]
  expected=sampled(m.floats(root/'A/atlas.rgba32f',m.W*m.H*4),1,0,mode)
  negative_error=max(abs(a-b) for a,b in zip(actual,expected))
  if negative_error<=.004:raise ValueError('sRGB negative was not detected')
  negatives[mode]=negative_error
 summary=dict(sampling_oracle_tolerance=.004,old_quality_limits_unchanged=True,status='MEASURED_NOT_QUALIFIED',samples_per_pixel=dict(binary16=256,linear4=16),acceptance='not pixel-perfect; no target-device performance qualification',mrt_scope='UNUSED preserve, not active MRT',negative_srgb_sampling_error=negatives,rows=rows)
 (out/'local-provenance.json').write_text(json.dumps({'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'integrate.frag',HERE/'run_lab.py']},'baseline_provenance':'baseline/local-provenance.json'},indent=2))
 (out/'comparison.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
