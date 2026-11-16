import json,pathlib,subprocess
import pytest
from tools import external_amber95119 as r
WARN='[WARNING] SPIR-V WARNING: Image Type operand of OpTypeSampledImage should not have a Dim of Buffer.\n'
def valid(name):
 if name in ('before','rollback'):return 1,'90: ComputeCommand\nSummary: 0 pass, 1 fail\n',WARN+'output buffer is not empty\n'+('[ERROR] VUID-vkDestroyDevice-device-05137\n'*2)
 if name=='after':return 0,'90: ComputeCommand\n92: ProbeSSBOCommand\n93: ProbeSSBOCommand\n94: ProbeSSBOCommand\nSummary: 1 pass, 0 fail\n',WARN
 return 1,'90: ComputeCommand\n92: ProbeSSBOCommand\nSummary: 0 pass, 1 fail\n',WARN+'Verifier failed: 2.000000 == 3.000000, at index 0\n'
@pytest.mark.parametrize('name',['before','after','rollback','wrong-expect'])
def test_baselines(name):r.verify_result(name,*valid(name))
@pytest.mark.parametrize('name',['before','after','rollback','wrong-expect'])
def test_wrong_exit(name):
 c,o,e=valid(name)
 with pytest.raises(ValueError):r.verify_result(name,not c,o,e)
@pytest.mark.parametrize('name',['before','after','rollback','wrong-expect'])
def test_added_vuid(name):
 c,o,e=valid(name)
 with pytest.raises(ValueError):r.verify_result(name,c,o,e+'VUID-unexpected-12345')
def test_missing_expect():
 c,o,e=valid('after')
 with pytest.raises(ValueError):r.verify_result('after',c,o.replace('94: ProbeSSBOCommand',''),e)
def test_wrong_mutant_value():
 c,o,e=valid('wrong-expect')
 with pytest.raises(ValueError):r.verify_result('wrong-expect',c,o,e.replace('2.000000','4.000000'))
def test_no_historical_runtime_error():
 c,o,e=valid('before')
 with pytest.raises(ValueError):r.verify_result('before',c,o,e.replace('output buffer is not empty',''))
@pytest.mark.parametrize('path',['/etc/passwd','../secret','a/../../secret'])
def test_escape(tmp_path,path):
 with pytest.raises(ValueError):r.local(tmp_path,path)
def test_symlink_escape(tmp_path):
 (tmp_path/'x').symlink_to('/etc');
 with pytest.raises(ValueError):r.local(tmp_path,'x/passwd')
def test_manifest_tamper(tmp_path):
 (tmp_path/'amber951-build-support').mkdir();(tmp_path/'amber951-build-support/final-manifest.json').write_text('{}')
 with pytest.raises(ValueError,match='manifest mismatch'):r.verify_artifacts(tmp_path)
def test_existing_output(tmp_path):
 with pytest.raises(ValueError,match='fresh'):r.run(tmp_path,tmp_path)
@pytest.mark.parametrize('timeout',[0,-1,True,121])
def test_invalid_timeout(tmp_path,timeout):
 with pytest.raises(ValueError,match='timeout'):r.run(tmp_path,tmp_path/'new',timeout)
def test_duplicate_json():
 with pytest.raises(ValueError):json.loads('{"a":1,"a":2}',object_pairs_hook=r.unique)
@pytest.fixture
def fake_cohort(tmp_path,monkeypatch):
 for v in ('before','after'):
  p=tmp_path/f'amber951-{v}-build/amber/amber';p.parent.mkdir(parents=True);p.write_text('fixture executable')
 p=tmp_path/'amber951-build-support';p.mkdir()
 for n in ('original.amber','wrong-expect.amber'):(p/n).write_text('fixture input')
 m={'environment':{'VK_DRIVER_FILES':'fixture','VK_LAYER_PATH':'fixture','LD_LIBRARY_PATH':'fixture','MESA_SHADER_CACHE_DISABLE':'true'}}
 monkeypatch.setattr(r,'verify_artifacts',lambda root:m)
 monkeypatch.setattr(r,'provenance_state',lambda:{'fixture':True})
 return tmp_path

def test_complete_mock_baseline(fake_cohort,monkeypatch):
 names=iter(['before','after','rollback','wrong-expect'])
 def proc(argv,**kwargs):
  assert 'LD_PRELOAD' not in kwargs['env']
  c,o,e=valid(next(names));return subprocess.CompletedProcess(argv,c,o.encode(),e.encode())
 monkeypatch.setenv('LD_PRELOAD','untrusted');monkeypatch.setattr(r.subprocess,'run',proc)
 report=r.run(fake_cohort,fake_cohort/'out')
 assert len(report['steps'])==4 and report['status']=='ORIGINAL_EXTERNAL_GPU_REGRESSION_REPRODUCED'

def test_timeout_no_success_partial_logs(fake_cohort,monkeypatch):
 def proc(argv,**kwargs):raise subprocess.TimeoutExpired(argv,1,output=b'partial',stderr=b'pending')
 monkeypatch.setattr(r.subprocess,'run',proc)
 with pytest.raises(subprocess.TimeoutExpired):r.run(fake_cohort,fake_cohort/'out',1)
 report=json.loads((fake_cohort/'out/report.json').read_text())
 assert report['status']=='BLOCKED' and report['steps'][0]['timed_out'] is True
 assert (fake_cohort/'out/before.stdout').read_bytes()==b'partial'
@pytest.mark.parametrize('text',['90: ComputeCommand\n','Summary: duplicate\n'])
def test_duplicate_compute_summary(text):
 c,o,e=valid('after')
 with pytest.raises(ValueError):r.verify_result('after',c,o+text,e)
def test_missing_compute():
 c,o,e=valid('after')
 with pytest.raises(ValueError):r.verify_result('after',c,o.replace('90: ComputeCommand\n',''),e)
