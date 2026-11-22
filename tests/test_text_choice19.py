"""HOST schema mutations. Synthetic metrics are not GPU or quality evidence."""
import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from tools import text_choice19 as r
pytestmark=pytest.mark.candidate19
def example():
 obs=[]
 for stage in ('board','refined','compact-400000','compact-200000'):
  for row in r.ROWS:
   if row=='emoji':continue
   modes=('bitmap','msdf') if stage in ('board','refined') else (('msdf',) if stage=='compact-400000' or row in ('combining','variable-light') else ('bitmap',))
   for mode in modes:
    for t in r.COMMON:obs.append(dict(stage=stage,row=row,representation=mode,transform=t,common_crop_width=65,common_crop_height=49,common_crop_y=0 if stage=='board' else 8,common_crop_mae=.01,common_crop_max=.1,sampling_error=0.,payload_bytes=(815360 if stage=='board' else (13045760 if stage=='refined' else r.COMPACT_COSTS[int(stage.split('-')[1])][row])),pixel_sha256='a'*64))
 return dict(schema='text-choice19-v1',device=dict(name='synthetic CPU fixture',api=4210993,device_type=4,vendor=65541,driver=1),observations=obs)
def policy():return dict(baseline='board/bitmap',quality_targets={'max_common_crop_mae':.02,'max_common_crop_error':.2},per_row_payload_budget=20000000,require_performance=False)
def test_baseline():assert r.decide(example(),policy())['status']=='KEEP_BASELINE'
def test_missing_target():
 p=policy();p['quality_targets']=None;assert r.decide(example(),p)['status']=='NEEDS_QUALITY_TARGET'
def test_performance():
 p=policy();p['require_performance']=True;assert r.decide(example(),p)['status']=='NEEDS_MEASUREMENT'
def test_budget():
 p=policy();p['per_row_payload_budget']=0;assert r.decide(example(),p)['status']=='NO_ADMISSIBLE_PATH'
@pytest.mark.parametrize('key,value',[('payload_bytes',True),('common_crop_width',65.),('common_crop_height',65),('common_crop_y',8),('common_crop_mae',float('nan')),('common_crop_max',10**1000),('row','other'),('transform','perspective')])
def test_mutation(key,value):
 e=example();assert r.decide(e,policy())['status']=='KEEP_BASELINE';e['observations'][0][key]=value;assert r.decide(e,policy())['status']=='UNKNOWN'
@pytest.mark.parametrize('kind',['missing','duplicate'])
def test_matrix(kind):
 e=example()
 if kind=='missing':e['observations'].pop()
 else:e['observations'][-1]=copy.deepcopy(e['observations'][0])
 assert r.decide(e,policy())['status']=='UNKNOWN'
def test_pass_is_not_evidence():assert r.decide({'status':'PASS'},policy())['status']=='UNKNOWN'

@pytest.fixture(scope='module')
def actual_roots():
 import os
 base=os.environ.get('TEXT_CHOICE19_RAW_ROOT')
 if not base:pytest.skip('explicit local fresh three-lab raw root required')
 return tuple(Path(base)/('text-board19-'+s)/'run' for s in ('baseline','refined','budget'))

@pytest.fixture(scope='module')
def actual_positive(actual_roots):
 result=r.analyze(*actual_roots,progress=lambda x:print(x,flush=True))
 assert len(result['observations'])==144 and result['positive_draws']==[53,66,86]
 return result

def test_actual_positive(actual_positive):
 p=policy();p['quality_targets']=None
 assert r.decide(actual_positive,p)['status']=='NEEDS_QUALITY_TARGET'

@pytest.mark.parametrize('kind',['wrong_font','wrong_scale','duplicate_row','duplicate_metric'])
def test_actual_metadata_mutations(actual_roots,actual_positive,monkeypatch,kind):
 import json
 original=Path.read_text
 def changed(path,*args,**kwargs):
  text=original(path,*args,**kwargs)
  if path==actual_roots[0]/('summary.json' if kind=='duplicate_metric' else 'frozen-input-manifest.json'):
   x=json.loads(text)
   if kind=='wrong_font':x[0]['layers'][0]['font_sha256']='0'*64
   elif kind=='wrong_scale':x[0]['ppem']+=1
   elif kind=='duplicate_row':x[-1]=copy.deepcopy(x[0])
   else:x['metrics'][-1]=copy.deepcopy(x['metrics'][0])
   return json.dumps(x)
  return text
 monkeypatch.setattr(Path,'read_text',changed)
 with pytest.raises(ValueError):r.analyze(*actual_roots)

def test_actual_pixel_mutation(actual_roots,actual_positive,monkeypatch):
 original=r.floats
 def changed(p,n):
  data=original(p,n)
  if Path(p)==actual_roots[0]/'gpu/chinese-native-0/color.rgba32f':data[0]+=.1
  return data
 monkeypatch.setattr(r,'floats',changed)
 with pytest.raises(ValueError,match='sampling error'):r.analyze(*actual_roots)
def test_duplicate_json():
 with pytest.raises(ValueError,match='duplicate JSON'):r.decode('{"a":1,"a":2}')
def test_actual_coordinated_pixel_summary_mutation(actual_roots,actual_positive,monkeypatch):
 import json
 original_floats=r.floats;original_read=Path.read_text
 def changed_pixels(p,n):
  data=original_floats(p,n)
  if Path(p)==actual_roots[0]/'gpu/chinese-native-0/color.rgba32f':data[0]+=.1
  return data
 def changed_summary(path,*args,**kwargs):
  text=original_read(path,*args,**kwargs)
  if path==actual_roots[0]/'summary.json':
   doc=json.loads(text)
   for m in doc['metrics']:
    if m['row']=='chinese' and m['transform']=='native' and m['representation']=='bitmap':m['max_composition_error']=0;m['sampling_pass']=True
   text=json.dumps(doc)
  return text
 monkeypatch.setattr(r,'floats',changed_pixels);monkeypatch.setattr(Path,'read_text',changed_summary)
 with pytest.raises(ValueError,match='sampling error'):r.analyze(*actual_roots)
def test_actual_device_log_identity(actual_roots,monkeypatch):
 import json
 assert r.device_cohort(actual_roots)['device_type']==4
 original=Path.read_text
 def changed(path,*a,**kw):
  text=original(path,*a,**kw)
  if path==actual_roots[0]/'gpu-correct.log':text=text.replace('vendor=65541','vendor=1')
  return text
 monkeypatch.setattr(Path,'read_text',changed)
 with pytest.raises(ValueError,match='same fixed'):r.device_cohort(actual_roots)
