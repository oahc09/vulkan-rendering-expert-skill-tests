import copy,json,sys,importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import resource_capture19 as r,resource_contract_chain19 as chain
pytestmark=pytest.mark.candidate19
def example():return json.loads((ROOT/'tests/fixtures/resource-capture19/good.json').read_text())
def test_complete_observed_unknown_and_declared():
 t=example();v=chain.check(t);assert v['status']=='OBLIGATIONS_NOT_ESTABLISHED' and v['submissions']==2
 t['obligations']={k:'CALLER_DECLARED' for k in r.OBLIGATIONS};assert chain.check(t)['status']=='CONSISTENT_DECLARED_TRACE'
@pytest.mark.parametrize('kind',['missing-input','wrong-generation','wrong-completion','delete-wait','early-free','duplicate','old-recording','update-binding','short-host-write','wrong-output','summary-spoof','float-generation','bool-generation','extra-reference','authority','depth','nan'])
def test_actual_capture_mutations(kind):
 t=example();assert r.check_v2(t)['status']=='OBLIGATIONS_NOT_ESTABLISHED'
 ev=t['events'];find=lambda op:[e for e in ev if e['op']==op]
 if kind=='missing-input':find('record_use')[0]['references'].pop(0)
 elif kind=='wrong-generation':find('record_use')[0]['references'][0]['generation']=2
 elif kind=='wrong-completion':find('complete')[0]['allocations']=[0]
 elif kind=='delete-wait':ev.remove(next(e for e in ev if e.get('call','').startswith('vkWaitForFences')))
 elif kind=='early-free':ev.insert(35,ev.pop(-2))
 elif kind=='duplicate':ev.insert(35,copy.deepcopy(ev[35]))
 elif kind=='old-recording':find('submit')[1]['recording']=0
 elif kind=='update-binding':find('descriptor_update')[0]['bindings'][1]['array_element']=1
 elif kind=='short-host-write':find('host_write')[-1]['size']=128
 elif kind in ('wrong-output','summary-spoof'):
  row=next(x for x in t['records'] if x['kind']=='readback');row['values'][0]+=1
  if kind=='summary-spoof':row['mismatches']=0
 elif kind=='float-generation':find('bind')[0]['generation']=1.0
 elif kind=='bool-generation':find('bind')[0]['generation']=True
 elif kind=='extra-reference':find('record_use')[0]['references'].append(copy.deepcopy(find('record_use')[0]['references'][0]))
 elif kind=='authority':t['obligations'][r.OBLIGATIONS[0]]='VERIFIED'
 elif kind=='depth':
  v={}
  for i in range(25):v={'x':v}
  t['extra']=v
 elif kind=='nan':find('bind')[0]['offset']=float('nan')
 for i,e in enumerate(ev):e['seq']=i # coordinate re-signing/re-indexing does not evade the semantic gate
 assert r.check_v2(t)['status']=='REJECTED_DECLARED_TRACE'
@pytest.mark.parametrize('raw',['{"x":1,"x":2}','{"x":NaN}','['*1000+'0'+']'*1000])
def test_entry_json_rejects(tmp_path,raw):
 spec=importlib.util.spec_from_file_location('entry',ROOT/'checks19/run_resource_capture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 p=tmp_path/'input';p.write_text(raw)
 with pytest.raises(ValueError):m.read_json(p)

def test_default_adaptation_never_promotes_capture():
 t=example();a=r.adapt(t['records'],t['events'],False)
 assert all(v=='UNRESOLVED' for v in a['obligations'].values())
 assert chain.check(a)['status']=='OBLIGATIONS_NOT_ESTABLISHED'
 assert chain.check(a)['observations']=='BOUNDED_CAPTURE_AND_OUTPUT_RECOMPUTED'

def test_wrong_oracle_actual_trace(tmp_path):
 # Stored good input/output cannot masquerade as the wrong-oracle execution.
 t=example();t['wrong']=True
 assert chain.check(t)['status']=='REJECTED_DECLARED_TRACE'
