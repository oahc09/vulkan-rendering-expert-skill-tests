"""Entry controls use mocked source loader only; real pinned run is separate."""
import pytest
from checks19 import run_image_layout_contracts as e
@pytest.fixture
def loaders(monkeypatch):
 monkeypatch.setattr(e.prose,'extract',lambda raw:{'fixture':True})
 entries={f'VUID-{owner}-{field}-{num}':[dict(vuid=f'VUID-{owner}-{field}-{num}',api_owner=owner,condition_key='core',page='chapters/synchronization.html')] for owner in ('VkImageMemoryBarrier','VkImageMemoryBarrier2') for field,num in [('oldLayout','01197'),('newLayout','01198')]}
 monkeypatch.setattr(e.spec,'load_pinned',lambda raw:dict(entries=entries,source={'fixture':True}))
def test_registered_controls(loaders):
 r=e.run(b'',b'');assert r['case_count']==17 and len(r['vuid_coordinates'])==4
 assert r['release_status']=='BLOCKED' and r['evidence_kind']=='CALLER_FACTS_HOST_CONTROLS_NOT_GPU'
 assert all(len(h)==64 for h in r['implementation_sha256'].values())
def test_broken_rule_rejected(loaders,monkeypatch):
 monkeypatch.setattr(e.rule,'evaluate',lambda *args:{'status':'PASS'})
 with pytest.raises(ValueError,match='control failed'):e.run(b'',b'')
def test_wrong_actual_source_rejected():
 with pytest.raises(ValueError,match='wrong frozen'):e.run(b'changed',b'{}')
def test_missing_coordinates_fail(loaders,monkeypatch):
 monkeypatch.setattr(e.spec,'load_pinned',lambda raw:dict(entries={},source={}))
 with pytest.raises(KeyError):e.run(b'',b'')
