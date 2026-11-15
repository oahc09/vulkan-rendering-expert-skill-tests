#!/usr/bin/env python3
import argparse,json,math,os,struct,subprocess,sys,hashlib
from pathlib import Path
from adapter import load,prepare
import reference as ref
from build import build
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,65
NAMES=['native','minified','rotate90','phase-quarter','phase-half','square-rotate90']
def floats(p,expected_count=16900):
 data=p.read_bytes()
 if len(data)!=expected_count*4:raise ValueError('exact float readback size')
 v=list(struct.unpack('<'+str(len(data)//4)+'f',data))
 if not all(math.isfinite(x) for x in v):raise ValueError('nonfinite readback')
 return v

def aux(folder):
 for name,expected in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
  v=floats(folder/(name+'.rgba32f'))
  if any(x!=expected[i%4] for i,x in enumerate(v)):raise ValueError('aux preservation')

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--variable-font',required=True,type=Path);p.add_argument('--msdf-source',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed '+log[-2000:])
  return log
 rows=prepare(a.variable_font)
 ep=load(HERE.parent/'text_emoji_lab/provider.py','board_ep');er=load(HERE.parent/'text_emoji_lab/run_lab.py','board_er');hb=load(ROOT/'tests/platform_text_probe.py','board_hb');ep.guard()
 if ep.policy('❤\ufe0f')!='emoji':raise ValueError('presentation route')
 shape=hb.shape(ep.FONT,'❤\ufe0f')
 if [g['id'] for g in shape['glyphs']]!=[168]:raise ValueError('actual VS16 shape identity')
 bgra=ep.decode(shape['glyphs'][0]['id']);run('png-reference',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),HERE.parent/'text_emoji_lab/png_reference.py',ep.FONT,out/'emoji.rgba']);png=(out/'emoji.rgba').read_bytes()
 if len(png)!=len(bgra) or any(bgra[i+c]!=(png[i+2-c]*png[i+3]+127)//255 for i in range(0,len(png),4) for c in range(3)) or any(bgra[i]!=png[i] for i in range(3,len(png),4)):raise ValueError('PNG byte reference mismatch')
 emoji=er.image_from_bgra(bgra,ep);emoji_ref=er.independent_png_reference(png)
 rows.insert(4,dict(name='emoji',text='❤\ufe0f',ppem='registered strike109 to34x32',receipts=[shape],layers=[dict(color=emoji)],advance=34,color=True))
 # Freeze real shape/layout and transform admission BEFORE any candidate GPU draw.
 manifest=[];jobs=[];unsupported=[]
 for row in rows:
  bounds=[p for l in row['layers'] for c in l.get('outline',[]) for e in c for p in e] if not row.get('color') else [(15,8),(49,40)]
  row['center']=[(min(p[k] for p in bounds)+max(p[k] for p in bounds))/2 for k in (0,1)];ref.CENTER=row['center']
  item={k:v for k,v in row.items() if k!='layers'};item['layers']=[{k:v for k,v in l.items() if k not in ('bitmap','color')} for l in row['layers']];item['transforms']={}
  for t,name in enumerate(NAMES):
   ok,why=ref.supported(row,t);item['transforms'][name]={'supported':ok,'reason':why}
   if not ok:unsupported.append(dict(row=row['name'],transform=name,reason=why));continue
   for mode in ([0] if row.get('color') else [0,1]):jobs.append((row,t,mode))
  manifest.append(item)
 baseline_identity=json.loads((HERE/'baseline-identity.json').read_text())
 for item in manifest:
  identity={k:item[k] for k in ['name','text','ppem','receipts','layers','advance']}
  digest=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if digest!=baseline_identity['row_identity_sha256'][item['name']]:raise ValueError('historical common layout identity changed')
 anchor_row=next(r for r in rows if r['name']=='variable-light');stem=anchor_row['layers'][1]
 if stem['glyph_id']!=553 or not any(set(tuple(p) for e in c for p in e)=={(24.5,22.75),(25.3125,22.75),(25.3125,32.),(24.5,32.)} for c in stem['outline']):raise ValueError('exact straight stem anchor changed')
 (out/'frozen-input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(out/'criteria.md').write_bytes((HERE/'criteria.md').read_bytes())
 b=out/'build';build(b,a.msdf_source,run)
 atlasdata={};paths={}
 for row in rows:
  folder=out/row['name'];folder.mkdir();bitmap=[];distance=[]
  for i,layer in enumerate(row['layers']):
   bitmap.append(layer['color'] if row.get('color') else [v for c in layer['bitmap'] for v in (c,c,c,1.)])
   if row.get('color'):continue
   contours=layer['outline'];lines=[str(len(contours))]
   for c in contours:
    lines.append(str(len(c)))
    for e in c:lines.append(str(len(e))+' '+' '.join(str(v) for pt in e for v in pt))
   path=folder/(str(i)+'.outline');path.write_text('\n'.join(lines)+'\n');target=folder/(str(i)+'.msdf');run('generate-'+row['name']+'-'+str(i),[b/'generate',path,target]);distance.append(floats(target,12740*16))
  for mode,layers in [(0,bitmap)]+([] if row.get('color') else [(1,distance)]):
   packed=layers if mode==1 else [[layer[(y*65+x)*4+c] if y<49 and x<65 else 0. for y in range(196) for x in range(260) for c in range(4)] for layer in layers]
   flat=[v for layer in packed for v in layer];flat += [0.]*(65*49*4*256-len(flat));path=folder/('bitmap.f32' if mode==0 else 'msdf.f32');path.write_bytes(struct.pack('<'+str(len(flat))+'f',*flat));paths[row['name'],mode]=path;atlasdata[row['name'],mode]=[list(struct.unpack('<'+str(len(layer))+'f',struct.pack('<'+str(len(layer))+'f',*layer))) for layer in layers]
 lines=[]
 for row,t,mode in jobs:
  name=row['name']+'-'+NAMES[t]+'-'+str(mode);lines.append(f'{name} {paths[row["name"],mode]} {t} {mode} {len(row["layers"])} {int(bool(row.get("color")))} {row["center"][0]} {row["center"][1]}')
 (out/'jobs.txt').write_text('\n'.join(lines)+'\n');log=run('gpu-correct',[b/'board',b/'correct',out/'jobs.txt',out/'gpu'])
 if 'validation_enabled=1' not in log:raise ValueError('validation not enabled')
 fb=type('Aux',(),{'aux':staticmethod(aux)})();preview=load(HERE.parent/'text_vector_lab/run_lab.py','board_preview');metrics=[];failed=[];phase_data={}
 for row,t,mode in jobs:
  ref.CENTER=row['center'];name=row['name']+'-'+NAMES[t]+'-'+str(mode);folder=out/'gpu'/name;fb.aux(folder);actual=floats(folder/'color.rgba32f')
  layers=[emoji_ref] if row.get('color') else atlasdata[row['name'],mode];expected=ref.expected(layers,t,mode,bool(row.get('color')));error=max(abs(x-y) for x,y in zip(actual,expected));tol=1e-6 if mode==0 else .004
  entry=dict(row=row['name'],transform=NAMES[t],representation='color-bitmap-fallback' if row.get('color') else ('bitmap' if mode==0 else 'msdf-linear4'),max_composition_error=error,tolerance=tol,excluded_pixels=0,sampling_pass=error<=tol)
  if not row.get('color'):
   geo=ref.outline_alpha(row['layers'],t);ac=[2*(actual[4*i+3]-.5) for i in range(4225)];diff=[abs(x-y) for x,y in zip(ac,geo)];roi=[i for i in range(4225) if geo[i]>0 or ac[i]>1e-5];edge_set=set()
   for layer in row['layers']:
    lc=ref.geometry(layer['outline'],t);edge_set.update(i for i,c in enumerate(lc) if 0<c<1)
   edge=sorted(edge_set);phase_data[row['name'],mode,t]=(ac,geo)
   entry.update(outline_alpha_mae=sum(diff)/4225,roi_mae=sum(diff[i] for i in roi)/len(roi),edge_mae=sum(diff[i] for i in edge)/len(edge) if edge else None,max_outline_alpha_error=max(diff),quality_status='MEASURED_NOT_QUALIFIED')
  metrics.append(entry)
  if error>tol:failed.append(name)
  def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
  preview.png(folder/'preview.png',65,65,bytes(enc(actual[4*i+c]) for i in range(4225) for c in range(3)))
 # Actual negative shaders on same registered ligature row; no changing layout.
 negatives={}
 for variant,mode in [('double-alpha',0),('wrong-range',1)]:
  row=next(r for r in rows if r['name']=='ligature');name='negative';jp=out/(variant+'.jobs');jp.write_text(f'{name} {paths[row["name"],mode]} 0 {mode} {len(row["layers"])} 0 {row["center"][0]} {row["center"][1]}\n')
  log=run('gpu-'+variant,[b/'board',b/variant,jp,out/variant]);folder=out/variant/name;fb.aux(folder);actual=floats(folder/'color.rgba32f');expected=ref.expected(atlasdata[row['name'],mode],0,mode);error=max(abs(x-y) for x,y in zip(actual,expected));negatives[variant]=error
  if 'validation_enabled=1' not in log or error<=(1e-6 if mode==0 else .004):raise ValueError('negative not detected '+variant)
 column_differences=[]
 for row in rows:
  if row.get("color"):continue
  for t in range(6):
   if (row["name"],0,t) not in phase_data:continue
   ba,_=phase_data[row["name"],0,t];ma,_=phase_data[row["name"],1,t];dif=[abs(x-y) for x,y in zip(ba,ma)]
   column_differences.append(dict(row=row["name"],transform=NAMES[t],alpha_mae=sum(dif)/4225,alpha_max=max(dif),status="MEASURED_NOT_QUALIFIED"))
 phase_residuals=[]
 for row in rows:
  if row.get('color'):continue
  for mode in (0,1):
   for ta,tb in [(0,3),(3,4)]:
    aa,ga=phase_data[row['name'],mode,ta];ab,gb=phase_data[row['name'],mode,tb]
    residual=[abs((ab[i]-aa[i])-(gb[i]-ga[i])) for i in range(4225)]
    phase_residuals.append(dict(row=row['name'],mode=mode,from_transform=NAMES[ta],to_transform=NAMES[tb],geometry_subtracted_mae=sum(residual)/4225,geometry_subtracted_max=max(residual),status='MEASURED_NOT_QUALIFIED'))
 run('contact-sheet',[os.environ.get('TEXT18_FONTTOOLS_PYTHON','python'),HERE/'contact_sheet.py',out])
 provenance={'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*HERE.glob('*.py'),HERE/'board.frag',HERE/'main.cpp',b/'board.hpp',b/'board',b/'generate']},'generator_commit':'1874bcf7d9624ccc85b4bc9a85d78116f690f35b','runtime_manifests':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep) if p},'provider_modules':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for sub in ['text_fallback_lab','text_variation_churn_lab','text_bidi_lab','text_emoji_lab'] for p in (HERE.parent/sub).glob('*.py')},'tools':{k:run('version-'+k,[os.environ.get(k,d),'--version']) for k,d in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]}}
 (out/'local-provenance.json').write_text(json.dumps(provenance,indent=2))
 prior_path=ROOT/'reports/history/text18-scene-a-board-public/numerical-summary.json'
 if hashlib.sha256(prior_path.read_bytes()).hexdigest()!=baseline_identity['report_sha256']:raise ValueError('historical report changed')
 prior=json.loads(prior_path.read_text())
 prior_index={(m['row'],m['transform'],m['representation']):m for m in prior['metrics']}
 comparisons=[]
 for m in metrics:
  old=prior_index.get((m['row'],m['transform'],m['representation']))
  if old and 'max_outline_alpha_error' in m:comparisons.append(dict(row=m['row'],transform=m['transform'],representation=m['representation'],before_max=old['max_outline_alpha_error'],after_max=m['max_outline_alpha_error'],before_roi_mae=old['roi_mae'],after_roi_mae=m['roi_mae']))
 anchor_pixels=floats(out/'gpu/variable-light-phase-half-1/color.rgba32f');anchor_alpha=2*(anchor_pixels[4*(31*65+25)+3]-.5)
 summary=dict(baseline_basis='historical frozen original report, not a same-run 1x execution',baseline_report_sha256=baseline_identity['report_sha256'],before_after=comparisons,anchor=dict(pixel=[25,31],exact_alpha=.609375,old_alpha=.123046875,new_alpha=anchor_alpha,new_error=abs(anchor_alpha-.609375),old_error=.486328125),validation_enabled=True,status='SAMPLING_PASS_QUALITY_NOT_QUALIFIED' if not failed else 'SAMPLING_NOT_QUALIFIED',rows=7,msdf_density=4,msdf_texel_range=16,screen_distance_range=4,texture_payload_bytes=13045760,output_size=[65,65],source_size=[260,196],texture_cost_vs_original=16,column_differences=column_differences,phase_residuals=phase_residuals,monochrome_glyph_layers=sum(len(r['layers']) for r in rows if not r.get('color')),positive_draws=len(jobs),unsupported=unsupported,metrics=metrics,negative_errors=negatives,failed_sampling_cases=failed,limits=['software Vulkan; no device performance','shared shaped layout; unhinted bitmap, not platform hinting','emoji color-bitmap-only; no forced outline','per-tile rendering in one logical Device, repeated uploads','perspective UNMEASURED','original-outline sampled reference, not exact area','aux UNUSED/preserve, not active MRT'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
 if failed:raise ValueError('sampling gates failed; evidence retained')
if __name__=='__main__':main()
