import pytest
from checks19 import run_memory_binding_contracts as e
@pytest.fixture
def mocked(monkeypatch):
 monkeypatch.setattr(e.prose,'extract',lambda raw:{'fixture':True})
 class Entries(dict):
  def __getitem__(self,k):return [dict(vuid=k,api_owner='fixture',condition_key='core',page='fixture',text_html='fixture')]
 monkeypatch.setattr(e.spec,'load_pinned',lambda raw:dict(source={},entries=Entries()))
def test_controls(mocked):
 r=e.run({},b'');assert r['case_count']==26 and r['release_status']=='BLOCKED'
def test_broken(mocked,monkeypatch):
 monkeypatch.setattr(e.rule,'bind',lambda *a:{'status':'PASS'})
 with pytest.raises(ValueError,match='control failed'):e.run({},b'')
def test_wrong_source():
 with pytest.raises(ValueError):e.run({'memory':b'x','resources':b'y'},b'{}')
