import argparse,json,struct,subprocess,os,sys,hashlib,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'scene_a_refined_board_lab'))
from adapter import load,prepare
import board_reference as ref
sys.path.pop(0)
from packing import crop,choose,pack
from build import build
NAMES=['native','minified','rotate90','phase-quarter','phase-half','square-rotate90','perspective']
def floats(p,n):
 b=p.read_bytes()
 if len(b)!=n*4:raise ValueError('exact input/readback length')
 v=list(struct.unpack('<'+str(n)+'f',b))
 if not all(math.isfinite(x) for x in v):raise ValueError('nonfinite float data')
 return v
def aux(p):
 for name,value in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  if any(x!=value[i%4] for i,x in enumerate(floats(p/(name+'.rgba32f'),16900))):raise ValueError('aux preservation')
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--variable-font',required=True,type=Path);p.add_argument('--msdf-source',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);src=a.source.resolve()
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise ValueError(name+' failed '+log[-1000:])
  return log
 rows=prepare(a.variable_font);old_manifest=json.loads((src/'frozen-input-manifest.json').read_text());old={r['name']:r for r in old_manifest};identity=json.loads((HERE.parent/'scene_a_refined_board_lab/baseline-identity.json').read_text())
 for row in rows:
  obj={k:row[k] for k in ['name','text','ppem','receipts','advance']};obj['layers']=[{k:v for k,v in l.items() if k!='bitmap'} for l in row['layers']]
  if hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=identity['row_identity_sha256'][row['name']]:raise ValueError('fresh source layout identity')
 # Independent PNG reference retained from verified prior source, decoded anew.
 er=load(HERE.parent/'text_emoji_lab/run_lab.py','compact_emoji');ep=load(HERE.parent/'text_emoji_lab/provider.py','compact_ep');ep.guard()
 run('png-reference',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),HERE.parent/'text_emoji_lab/png_reference.py',ep.FONT,out/'emoji.rgba']);emoji=er.independent_png_reference((out/'emoji.rgba').read_bytes())
 rows.insert(4,dict(name='emoji',color=True,layers=[dict(color=emoji)]))
 for row in rows:
  points=[p for l in row['layers'] for c in l.get('outline',[]) for e in c for p in e] if not row.get('color') else [(14,7),(50,41)]
  if any(not(0<ref.transform(x,y,6)[0]<65 and 0<ref.transform(x,y,6)[1]<65) for x,y in points):raise ValueError('registered perspective ink footprint clipped')
 plans=[];rejected=0
 for row in rows:
  crops=[crop(l,row.get('color',False)) for l in row['layers']]
  try:choose(crops,4096,row.get('color',False))
  except ValueError as e:
   if str(e)!='texture payload budget cannot fit bitmap fallback':raise
   rejected+=1
  else:raise ValueError('small budget did not reject')
  for budget in [400000,200000]:plans.append((row,choose(crops,budget,row.get('color',False))))
 (out/'plans.json').write_text(json.dumps([dict(row=r['name'],**p) for r,p in plans],indent=2));(out/'criteria.md').write_bytes((HERE/'criteria.md').read_bytes());b=out/'build';build(b,a.msdf_source,run)
 preview=load(HERE.parent/'text_vector_lab/run_lab.py','compact_preview');metrics=[];neg=[];negative_geometry=[]
 for row,plan in plans:
  name=row['name'];key=name+'-'+str(plan['budget']);folder=out/key;folder.mkdir();mode=plan['mode'];layers=[]
  for i,l in enumerate(row['layers']):
   if mode==2:layers.append(emoji)
   elif mode==0:layers.append([v for c in l['bitmap'] for v in (c,c,c,1)])
   else:
    contours=l['outline'];lines=[str(len(contours))]
    for c in contours:
     lines.append(str(len(c)))
     for e in c:lines.append(str(len(e))+' '+' '.join(str(v) for point in e for v in point))
    outline=folder/(str(i)+'.outline');outline.write_text('\n'.join(lines)+'\n');target=folder/(str(i)+'.msdf');run('generate-'+key+'-'+str(i),[b/'generate',outline,target]);layers.append(floats(target,203840))
  data=pack(plan,layers);atlas=folder/'atlas.f32';atlas.write_bytes(struct.pack('<'+str(len(data))+'f',*data));jobs=[];ts=[]
  for t in range(7):
   supported=(t!=2 or bool(row.get('color')))
   if t<6 and old[name]['transforms'][NAMES[t]]['supported']!=supported:raise ValueError('frozen admitted transform set changed')
   if not supported:continue
   ts.append(t);jobs.append(f'{NAMES[t]} {atlas} {t} {int(mode==1)} {len(layers)} {int(mode==2)} 32.5 24.5')
  jp=folder/'jobs.txt';jp.write_text('\n'.join(jobs)+'\n');log=run(key,[b/'compact_lab',b/'compact',jp,folder/'gpu',plan['width'],plan['height']])
  if 'validation_enabled=1' not in log:raise ValueError('validation required')
  for t in ts:
   gpu=folder/'gpu'/NAMES[t];aux(gpu);actual=floats(gpu/'color.rgba32f',16900);expected=ref.expected(layers,t,int(mode==1),mode==2);err=max(abs(x-y) for x,y in zip(actual,expected));tol=.004 if mode==1 else 1e-6
   historical_mode=0 if mode in (0,2) else 1
   historic=src/'gpu'/(name+'-'+NAMES[t]+'-'+str(historical_mode))/'color.rgba32f';past=floats(historic,16900) if t<6 else None;delta=max(abs(x-y) for x,y in zip(actual,past)) if past else None
   m=dict(historical_full_gpu_max_delta=delta,row=name,budget=plan['budget'],mode=mode,transform=NAMES[t],payload_bytes=plan['payload_bytes'],max_composition_error=err,tolerance=tol,excluded_pixels=0)
   if mode!=2:
    geo=ref.outline_alpha(row['layers'],t);ac=[2*(actual[4*i+3]-.5) for i in range(4225)];diff=[abs(x-y) for x,y in zip(ac,geo)];roi=[i for i in range(4225) if geo[i]>0 or ac[i]>1e-5];m.update(max_outline_alpha_error=max(diff),roi_mae=sum(diff[i] for i in roi)/len(roi))
   if name=='bidi' and t==4:
    alpha=2*(actual[4*(37*65+55)+3]-.5);m.update(exact_anchor_alpha=.43560791015625,actual_anchor_alpha=alpha,exact_anchor_error=abs(alpha-.43560791015625),old_16x_reference_alpha=.3955078125)
   metrics.append(m)
   if err>tol:raise ValueError('compact sampling gate failed '+key+NAMES[t]+' '+str(err))
   def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
   preview.png(gpu/'preview.png',65,65,bytes(enc(actual[4*i+c]) for i in range(4225) for c in range(3)))
  if name=='ligature' and plan['budget']==400000:
   jp=folder/'negative.jobs';jp.write_text(jobs[0]+'\n');run('wrong-metadata',[b/'compact_lab',b/'wrong-metadata',jp,folder/'negative',plan['width'],plan['height']]);gpu=folder/'negative'/NAMES[ts[0]];aux(gpu);actual=floats(gpu/'color.rgba32f',16900);expected=ref.expected(layers,ts[0],1);e=max(abs(x-y) for x,y in zip(actual,expected))
   if e<=.004:raise ValueError('wrong metadata accepted')
   neg.append(e)
   jp=folder/'inverse.jobs';jp.write_text(jobs[-1]+'\n');run('wrong-inverse',[b/'compact_lab',b/'wrong-inverse',jp,folder/'inverse-negative',plan['width'],plan['height']]);gpu=folder/'inverse-negative'/'perspective';aux(gpu);actual=floats(gpu/'color.rgba32f',16900);expected=ref.expected(layers,6,1);e=max(abs(x-y) for x,y in zip(actual,expected))
   if e<=.004:raise ValueError('affine inverse negative accepted')
   geo=ref.outline_alpha(row['layers'],6);positive=floats(folder/'gpu/perspective/color.rgba32f',16900)
   negative_geometry.append(dict(kind='wrong-inverse',wrong_outline_mae=sum(abs(2*(actual[4*i+3]-.5)-geo[i]) for i in range(4225))/4225,correct_outline_mae=sum(abs(2*(positive[4*i+3]-.5)-geo[i]) for i in range(4225))/4225,max_alpha_difference=max(abs(actual[4*i+3]-positive[4*i+3])*2 for i in range(4225))))
   neg.append(e)
 provenance={'authored_sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*.py'),HERE/'compact.frag',HERE/'perspective.vert',b/'board.hpp',b/'compact.cpp',b/'compact_lab']},'prior_manifest_sha256':hashlib.sha256((src/'frozen-input-manifest.json').read_bytes()).hexdigest(),'runtime_manifests':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep) if p},'tools':{k:run('version-'+k,[os.environ.get(k,d),'--version']) for k,d in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]}}
 (out/'local-provenance.json').write_text(json.dumps(provenance,indent=2))
 if len(metrics)!=86 or len(plans)!=14 or len(neg)!=2:raise ValueError('incomplete registered board execution')
 summary=dict(status='SAMPLING_PASS_QUALITY_NOT_QUALIFIED',validation_enabled=True,plans=[dict(row=r['name'],**p) for r,p in plans],metrics=metrics,rejected_before_gpu=rejected,metadata_negative_errors=neg,negative_kinds=['wrong-metadata','wrong-inverse'],negative_geometry=negative_geometry,limits=['compact storage, not adaptive density','per-row independent logical Device, transformations share row image','budget counts actual texture W*H*16 incl header/padding, not native VRAM allocation','source MSDF freshly generated full CPU images before crop, not CPU peak optimization','bounded real projected quad with stable inverse sampling; no hardware varying interpolation claim','bitmap fallback may degrade quality'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
