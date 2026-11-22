import pytest
from checks19 import run_timeline_contracts as e
@pytest.fixture
def loaders(monkeypatch):
 monkeypatch.setattr(e.prose,'extract',lambda raw:{'fixture':True})
 ids=[f'VUID-VkSemaphoreSignalInfo-value-{v}' for v in ('03258','03259','03260')]+['VUID-vkDestroySemaphore-semaphore-05149']
 monkeypatch.setattr(e.spec,'load_pinned',lambda raw:{'source':{},'entries':{v:[dict(vuid=v,api_owner='fixture',condition_key='core',page='sync')] for v in ids}})
def test_controls(loaders):
 r=e.run(b'',b'');assert r['case_count']==14 and r['release_status']=='BLOCKED' and len(r['vuid_coordinates'])==4
def test_broken_rule(loaders,monkeypatch):
 monkeypatch.setattr(e.rule,'host_signal',lambda *a:{'status':'PASS'})
 with pytest.raises(ValueError,match='control failed'):e.run(b'',b'')
def test_wrong_source():
 with pytest.raises(ValueError,match='wrong frozen'):e.run(b'wrong',b'{}')
