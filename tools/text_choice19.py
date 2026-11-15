"""Bounded seven-row text evidence and policy. Not visual qualification or GPU timing.

Reference code is the registered original independent CPU sampler/outline model;
this wrapper is not an independent font shaper or analytic curved-area oracle.
"""
import hashlib, importlib.util, json, math, struct, subprocess, tempfile, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROWS=('chinese','ligature','combining','bidi','emoji','variable-light','variable-heavy')
TRANSFORMS=('native','minified','rotate90','phase-quarter','phase-half','square-rotate90','perspective')
COMMON=('native','minified','phase-quarter','phase-half')
COMPACT_COSTS={400000:dict(zip(ROWS,(296448,249216,101184,369600,20160,168960,211200))),200000:dict(zip(ROWS,(18816,15840,101184,32592,20160,168960,13440)))}
LABS=('scene_a_board_lab','scene_a_refined_board_lab','scene_a_budget_board_lab')
def require(ok,why):
 if not ok: raise ValueError(why)
def decode(text):
 def pairs(items):
  result={}
  for k,v in items:
   require(k not in result,'duplicate JSON key');result[k]=v
  return result
 return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def floats(path,n):
 b=Path(path).read_bytes();require(len(b)==n*4,'pixel/atlas length');v=list(struct.unpack('<'+'f'*n,b));require(all(math.isfinite(x) for x in v),'nonfinite pixel');return v
def aux(folder,n):
 for name,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:require(all(x==values[i%4] for i,x in enumerate(floats(folder/(name+'.rgba32f'),n))),'aux preservation')
def maximum(a,b):
 require(len(a)==len(b),'reference size');return max(abs(x-y) for x,y in zip(a,b))
def manifest(path):
 rows=decode(Path(path).read_text());require(type(rows)is list and [r.get('name') for r in rows]==list(ROWS),'registered rows/order')
 pinned=decode((ROOT/'tests/fixtures/scene_a_refined_board_lab/baseline-identity.json').read_text())['row_identity_sha256']
 for r in rows:
  identity={k:r[k] for k in ('name','text','ppem','receipts','layers','advance')};require(canonical(identity)==pinned[r['name']],'font/layout/axis/scale identity')
 return rows

def device_cohort(roots):
 identities=[]
 for root in map(Path,roots):
  for path in root.rglob('*.log'):
   text=path.read_text()
   require('VALIDATION:' not in text,'validation diagnostic')
   if 'validation_enabled=' not in text:continue
   headers=[decode(line) for line in text.splitlines() if line.startswith('{') and '"deviceType"' in line]
   matches=re.findall(r'validation_enabled=(\d+) jobs=(\d+) vendor=(\d+) driver=(\d+)',text)
   require(len(headers)==1 and len(matches)==1,'actual device log identity')
   h=headers[0];v,j,vendor,driver=map(int,matches[0]);require(v==1 and j>0 and type(h['deviceType'])is int and h['deviceType']==4 and type(h['apiVersion'])is int and h['validation']==1,'CPU validation cohort')
   identities.append(dict(name=h['device'],api=h['apiVersion'],device_type=h['deviceType'],vendor=vendor,driver=driver))
 require(len(identities)==22 and all(x==identities[0] for x in identities),'same fixed software device identity across 22 invocations')
 return identities[0]

def analyze(board,refined,budget,progress=None):
 """Read full raw artifacts. No PASS/status flag establishes quality or source trust.
 Caller must separately verify exact source/tool/font cohort and raw inventory.
 """
 roots=list(map(Path,(board,refined,budget)));identity=device_cohort(roots);rows=manifest(roots[0]/'frozen-input-manifest.json');rrows=manifest(roots[1]/'frozen-input-manifest.json')
 require([{k:r[k] for k in ('name','text','ppem','receipts','layers','advance')} for r in rows]==[{k:r[k] for k in ('name','text','ppem','receipts','layers','advance')} for r in rrows],'common layout')
 refs=[module('text_ref_'+str(i),ROOT/'tests/fixtures'/lab/('board_reference.py' if i==2 else 'reference.py')) for i,lab in enumerate(LABS)]
 packing=module('text_pack',ROOT/'tests/fixtures'/LABS[2]/'packing.py')
 summaries=[decode((r/'summary.json').read_text()) for r in roots]
 observations=[];negatives={};layers_by={};pixels={};geometry={}
 emoji_lab=ROOT/'tests/fixtures/text_emoji_lab';provider=module('choice_emoji_provider',emoji_lab/'provider.py');provider.guard()
 er=module('choice_emoji_ref',emoji_lab/'run_lab.py')
 with tempfile.TemporaryDirectory(prefix='text-choice-png-') as d:
  target=Path(d)/'emoji.rgba';decoded=subprocess.run(['/usr/bin/python3',str(emoji_lab/'png_reference.py'),str(provider.FONT),str(target)],capture_output=True,timeout=60)
  require(decoded.returncode==0,'independent PNG decode');png=target.read_bytes();require(len(png)==136*128*4,'PNG size')
 require(all((root/'emoji.rgba').read_bytes()==png for root in roots),'independent PNG bytes')
 emoji_reference=er.independent_png_reference(png)
 for stage,root in enumerate(roots[:2]):
  require(all('validation_enabled=1' in (root/('gpu-'+label+'.log')).read_text() for label in ('correct','double-alpha','wrong-range')),'validation enabled log')
  expected_summary={(r['name'],TRANSFORMS[t],('color-bitmap-fallback' if r['name']=='emoji' else ('bitmap' if mode==0 else 'msdf-linear4'))) for r in rows for t in range(5+stage) if t!=2 or r['name']=='emoji' for mode in ([0] if r['name']=='emoji' else [0,1])}
  ms=summaries[stage]['metrics'];require(len(ms)==len(expected_summary) and {(m['row'],m['transform'],m['representation']) for m in ms}==expected_summary,'summary registered keys')
  unsupported=summaries[stage]['unsupported'];require(len(unsupported)==6 and {(m['row'],m['transform']) for m in unsupported}=={(r,'rotate90') for r in ROWS if r!='emoji'},'unsupported registry')
  require(set(summaries[stage]['negative_errors'])=={'double-alpha','wrong-range'},'negative registry')
 for stage,(root,ref) in enumerate(zip(roots[:2],refs[:2])):
  h=49 if stage==0 else 65;n=65*h*4;expected_keys=[]
  for row in rows:
   name=row['name'];color=name=='emoji';count=len(row['layers'])
   for mode in ([0] if color else [0,1]):
    # Refined bitmap remains 1x data within padded 4x allocation.
    stride=12740*(16 if stage==1 and mode==1 else 1)
    total=12740*16*(16 if stage else 1)
    atlas=floats(root/name/('bitmap.f32' if mode==0 else 'msdf.f32'),total)
    layers=[atlas[i*stride:(i+1)*stride] for i in range(count)]
    if stage==1 and mode==0:layers=[[atlas[i*203840+4*(y*260+x)+c] for y in range(49) for x in range(65) for c in range(4)] for i in range(count)]
    if color:
     require(maximum(layers[0],emoji_reference)<=1e-7,'emoji independent input reference')
     layers=[list(struct.unpack('<12740f',struct.pack('<12740f',*emoji_reference)))]
    layers_by[stage,name,mode]=layers
    for t in range(5+stage):
     if t==2 and not color:continue
     key=name+'-'+TRANSFORMS[t]+'-'+str(mode);expected_keys.append(key);folder=root/'gpu'/key;actual=floats(folder/'color.rgba32f',n);aux(folder,n)
     expected=ref.expected(layers,t,mode,color);err=maximum(actual,expected);require(err<=(1e-6 if mode==0 else .004),'sampling error '+key)
     pixels[stage,name,t,mode]=actual
     declared=next(m for m in summaries[stage]['metrics'] if m['row']==name and m['transform']==TRANSFORMS[t] and m['representation']==('color-bitmap-fallback' if color else ('bitmap' if mode==0 else 'msdf-linear4')))
     require(type(declared['max_composition_error'])in (int,float) and abs(declared['max_composition_error']-err)<1e-7 and declared['tolerance']==(1e-6 if mode==0 else .004) and declared['excluded_pixels']==0 and declared['sampling_pass']is True,'sampling summary mismatch')
     if not color and TRANSFORMS[t] in COMMON:
      gkey=(name,t)
      if gkey not in geometry:geometry[gkey]=refs[0].outline_alpha(row['layers'],t)
      crop=[2*(actual[4*((y+(8 if stage else 0))*65+x)+3]-.5) for y in range(49) for x in range(65)]
      diff=[abs(a-b) for a,b in zip(crop,geometry[gkey])]
      observations.append(dict(stage=('board','refined')[stage],row=name,representation='bitmap' if mode==0 else 'msdf',transform=TRANSFORMS[t],common_crop_width=65,common_crop_height=49,common_crop_y=8 if stage else 0,common_crop_mae=sum(diff)/3185,common_crop_max=max(diff),sampling_error=err,payload_bytes=total*4,pixel_sha256=sha(folder/'color.rgba32f')))
   if progress:progress(('board','refined')[stage]+'/'+name)
  require(sorted(p.name for p in (root/'gpu').iterdir())==sorted(expected_keys),'full registered GPU matrix')
  require(len(summaries[stage]['metrics'])==len(expected_keys),'summary matrix count')
  for variant,mode in [('double-alpha',0),('wrong-range',1)]:
   folder=root/variant/'negative';actual=floats(folder/'color.rgba32f',n);aux(folder,n);err=maximum(actual,ref.expected(layers_by[stage,'ligature',mode],0,mode));require(err>(1e-6 if mode==0 else .004),'actual negative not detected');negatives[str(stage)+'/'+variant]=err;require(abs(summaries[stage]['negative_errors'][variant]-err)<1e-12,'negative summary mismatch')
 # Compact: reconstruct exact packing from original fresh full layers, not metadata as oracle.
 plans=decode((roots[2]/'plans.json').read_text());expected_plans=[];keys=[]
 for row in rows:
  name=row['name'];color=name=='emoji';crops=[packing.crop(l,color) for l in row['layers']]
  try:packing.choose(crops,4096,color)
  except ValueError:pass
  else:raise ValueError('4096 must reject before GPU')
  for limit in (400000,200000):
   require('validation_enabled=1' in (roots[2]/(name+'-'+str(limit)+'.log')).read_text(),'compact validation enabled')
   plan=packing.choose(crops,limit,color);expected_plans.append(dict(row=name,**plan));mode=plan['mode'];folder=roots[2]/(name+'-'+str(limit));layers=layers_by[1,name,0 if mode in (0,2) else 1]
   packed=floats(folder/'atlas.f32',plan['width']*plan['height']*4);require(packed==packing.pack(plan,layers),'compact payload/source mismatch')
   for t in range(7):
    if t==2 and not color:continue
    keys.append((name,limit,TRANSFORMS[t]));gpu=folder/'gpu'/TRANSFORMS[t];actual=floats(gpu/'color.rgba32f',16900);aux(gpu,16900);expected=refs[2].expected(layers,t,int(mode==1),color);err=maximum(actual,expected);require(err<=(.004 if mode==1 else 1e-6),'compact sampling error')
    declared=next(m for m in summaries[2]['metrics'] if m['row']==name and m['budget']==limit and m['transform']==TRANSFORMS[t]);require(type(declared['max_composition_error'])in (int,float) and abs(declared['max_composition_error']-err)<1e-7 and declared['tolerance']==(.004 if mode==1 else 1e-6) and type(declared['excluded_pixels'])is int and declared['excluded_pixels']==0,'compact sampling summary mismatch')
    if not color and TRANSFORMS[t] in COMMON:
     crop=[2*(actual[4*((y+8)*65+x)+3]-.5) for y in range(49) for x in range(65)];diff=[abs(a-b) for a,b in zip(crop,geometry[name,t])]
     observations.append(dict(stage='compact-'+str(limit),row=name,representation='msdf' if mode==1 else 'bitmap',transform=TRANSFORMS[t],common_crop_width=65,common_crop_height=49,common_crop_y=8,common_crop_mae=sum(diff)/3185,common_crop_max=max(diff),sampling_error=err,payload_bytes=plan['payload_bytes'],pixel_sha256=sha(gpu/'color.rgba32f')))
   require({x.name for x in (folder/'gpu').iterdir()}=={TRANSFORMS[t] for t in range(7) if t!=2 or color},'compact GPU directory registry')
   if progress:progress('compact/'+name+'/'+str(limit))
   if name=='ligature' and limit==400000:
    for variant,sub,t in [('wrong-metadata','negative',0),('wrong-inverse','inverse-negative',6)]:
     gpu=folder/sub/TRANSFORMS[t];actual=floats(gpu/'color.rgba32f',16900);aux(gpu,16900);err=maximum(actual,refs[2].expected(layers,t,1));require(err>.004,'compact negative not detected');negatives['2/'+variant]=err
 require(len(summaries[2]['metadata_negative_errors'])==2 and all(abs(a-b)<1e-12 for a,b in zip(summaries[2]['metadata_negative_errors'],[negatives['2/wrong-metadata'],negatives['2/wrong-inverse']])),'compact negative summary')
 require(plans==expected_plans and summaries[2]['plans']==expected_plans,'exact compact plans')
 require(len(keys)==86 and {(m['row'],m['budget'],m['transform']) for m in summaries[2]['metrics']}==set(keys) and len(summaries[2]['metrics'])==86,'compact complete matrix')
 require(summaries[2]['rejected_before_gpu']==7,'precreation rejects')
 for root in roots:
  for log in root.rglob('*.log'):require('VALIDATION:' not in log.read_text(),'validation diagnostic')
 return dict(schema='text-choice19-v1',device=identity,observations=observations,actual_shader_negatives=negatives,positive_draws=[53,66,86],precreation_rejected_rows=7,scope='six monochrome rows/four common transforms; emoji bitmap-only separately verified; sampled outline not analytic curved coverage; no performance',manifest_sha256=sha(roots[0]/'frozen-input-manifest.json'))

def decide(evidence,policy):
 """No policy can certify a record's origin. Strict wrapper re-runs analyze first."""
 try:
  require(type(evidence)is dict and evidence['schema']=='text-choice19-v1','evidence schema')
  device=evidence['device'];require(type(device)is dict and set(device)=={'name','api','device_type','vendor','driver'} and type(device['name'])is str and bool(device['name']) and all(type(device[k])is int and 0<=device[k]<2**32 for k in ('api','device_type','vendor','driver')) and device['device_type']==4,'device scope')
  obs=evidence['observations'];require(type(obs)is list and len(obs)==144,'observations matrix')
  registered={(s,r,t,m) for s in ('board','refined') for r in ROWS if r!='emoji' for t in COMMON for m in ('bitmap','msdf')}|{('compact-'+str(b),r,t,('msdf' if b==400000 or r in ('combining','variable-light') else 'bitmap')) for b in (400000,200000) for r in ROWS if r!='emoji' for t in COMMON}
  require({(o['stage'],o['row'],o['transform'],o['representation']) for o in obs}==registered,'registered observation keys')
  for o in obs:
   require(set(o)=={'stage','row','representation','transform','common_crop_width','common_crop_height','common_crop_y','common_crop_mae','common_crop_max','sampling_error','payload_bytes','pixel_sha256'},'observation fields')
   cost=815360 if o['stage']=='board' else (13045760 if o['stage']=='refined' else COMPACT_COSTS[int(o['stage'].split('-')[1])][o['row']])
   require(type(o['payload_bytes'])is int and o['payload_bytes']==cost,'registered payload cost')
   require(type(o['pixel_sha256'])is str and re.fullmatch('[0-9a-f]{64}',o['pixel_sha256']) is not None,'pixel digest')
   require(type(o['common_crop_width'])is int and o['common_crop_width']==65 and type(o['common_crop_height'])is int and o['common_crop_height']==49,'common crop denominator')
   require(type(o['common_crop_y'])is int and o['common_crop_y']==(0 if o['stage']=='board' else 8),'crop registration')
   for k in ('common_crop_mae','common_crop_max','sampling_error'):require(type(o[k])in (int,float) and 0<=o[k]<=1 and math.isfinite(o[k]),'finite metric')
   require(o['sampling_error']<=(1e-6 if o['representation']=='bitmap' else .004),'sampling quality gate')
  require(type(policy)is dict and set(policy)=={'baseline','quality_targets','per_row_payload_budget','require_performance'},'policy schema')
  require(policy['baseline']=='board/bitmap' and type(policy['per_row_payload_budget'])is int and 0<=policy['per_row_payload_budget']<2**63 and type(policy['require_performance'])is bool,'policy types')
  target=policy['quality_targets']
  if target is None:return dict(status='NEEDS_QUALITY_TARGET',eligible=[],fallback='not qualified')
  require(type(target)is dict and set(target)=={'max_common_crop_mae','max_common_crop_error'},'quality target names')
  for v in target.values():require(type(v)in (int,float) and 0<=v<=1 and math.isfinite(v),'quality target finite')
  groups={}
  for o in obs:groups.setdefault(o['stage']+('/registered-plan' if o['stage'].startswith('compact-') else '/'+o['representation']),[]).append(o)
  eligible=[k for k,v in groups.items() if all(o['payload_bytes']<=policy['per_row_payload_budget'] and o['common_crop_mae']<=target['max_common_crop_mae'] and o['common_crop_max']<=target['max_common_crop_error'] for o in v)]
  # Compact plans are heterogeneous per row; never qualify a partial representation as the board.
  eligible=[k for k in eligible if len(groups[k])==24]
  return dict(status='NEEDS_MEASUREMENT' if policy['require_performance'] and eligible else ('KEEP_BASELINE' if 'board/bitmap' in eligible else ('QUALIFIED_CANDIDATE_SET' if eligible else 'NO_ADMISSIBLE_PATH')),eligible=eligible,qualification_scope='six monochrome rows x four common transforms only; emoji and new transforms not product-qualified',fallback='board/bitmap' if 'board/bitmap' in eligible else None)
 except (ValueError,KeyError,TypeError,OverflowError):return dict(status='UNKNOWN',eligible=[])
