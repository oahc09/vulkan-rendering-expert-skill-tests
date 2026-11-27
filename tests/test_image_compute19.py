"""Recorded real integration evidence/source binding, not a fresh GPU execution."""
import hashlib,json
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
ROOT=Path(__file__).parents[1]
D=json.loads((ROOT/'coverage/v1.0.19/image-compute.json').read_text())
CASE=ROOT/'cases19/image_compute'
@pytest.mark.parametrize('path,key',[('baseline.c',('repair','baseline_sha256')),('fix.patch',('repair','patch_sha256')),('compute.comp',('shader','source_sha256')),('run.py',('runner_sha256',))])
def test_source_binding(path,key):
 value=D
 for k in key:value=value[k]
 assert hashlib.sha256((CASE/path).read_bytes()).hexdigest()==value
@pytest.mark.parametrize('name',list(D['cases']))
def test_same_artifact_and_runtime_manifest(name):
 c=D['cases'][name];m=c['actual_manifest']
 assert c['shader_sha256']==D['shader']['spirv_sha256']
 assert m['IDENTITY']==[D['identity']]
 assert m['INPUT']==[[i*11+5 for i in range(16)]]
 assert m['IMAGE_QUERY'][0]['usage']==11
 assert len(m['IMAGE_MEMORY'])==len(m['MEMORY'])==2
 assert m['DESCRIPTOR']==[dict(set=0,binding=i,type=3,count=1,stage=32,imageLayout=1,image=i) for i in range(2)]
 if name in ('good','wrong-output'):
  assert c['result']['submitted'] is True and c['result']['errors']==0
  assert c['result']['pixels']==[(i*11+5)*3+7 for i in range(16)]
  assert c['result']['exit_code']==(6 if name=='wrong-output' else 0)
  assert m['COMPLETION'][0]['fence_wait']=='SUCCESS'
 else:
  assert c['result']['submitted'] is False
  assert c['result']['errors']==len(c['diagnostics'])>0
  assert c['result']['exit_code']==0 and not m['COMPLETION']
def test_heuristic_off_is_not_pass():
 o=D['heuristic_off_observation'];r=o['result']
 assert o['status']=='HAZARD_NOT_DETECTED_NOT_PASS'
 assert r['mode']=='normal' and r['upload_dependency']==0
 assert r['exit_code']==o['log']['exit_code']==5
 assert r['errors']==0 and r['submitted'] is False
 assert o['binary_sha256']==D['repair']['baseline_binary_sha256']
def test_oracle_and_diagnostics_are_separate():
 assert D['cases']['good']['status']=='ALL_PIXELS_EXACT_PASS'
 assert D['cases']['wrong-output']['status']=='EXPECTED_ORACLE_FAILURE'
 for name in ('missing-upload-dependency','missing-readback-dependency'):
  assert 'SYNC-HAZARD-READ-AFTER-WRITE' in str(D['cases'][name]['diagnostics'])
 assert '00344' in str(D['cases']['bad-layout']['diagnostics'])
 assert '08114' in str(D['cases']['bad-layout']['diagnostics'])
def test_stage_does_not_promote_original_tasks_or_hardware():
 tasks=json.loads((ROOT/'coverage/v1.0.19/tasks.json').read_text())
 assert len(tasks)==36 and all(x['status']=='UNVERIFIED' for x in tasks)
 domains=json.loads((ROOT/'coverage/v1.0.19/domains.json').read_text())
 for d in domains:
  if d['id'] in ('VK05','VK06'):assert d['image_compute_delivery']['domain_complete'] is False
 assert any('noncoherent' in x for x in D['limitations'])
