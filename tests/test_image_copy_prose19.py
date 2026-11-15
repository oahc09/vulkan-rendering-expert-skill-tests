import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from tools import image_copy_prose19 as p
@pytest.fixture
def source(monkeypatch):
 data={name:(''.join('[['+a+']]\ntext\n' for a in anchors)+('include::{chapters}/commonvalidity/copy_image_common.adoc[]\n' if name=='copies' else '')).encode() for name,(path,digest,anchors) in p.SOURCES.items()}
 monkeypatch.setattr(p,'SOURCES',{name:(path,p.sha(data[name]),anchors) for name,(path,digest,anchors) in p.SOURCES.items()});return data
def test_all_sources(source):
 r=p.map_sources(source);assert r['status']=='PINNED_IMAGE_COPY_PROSE_MAP';assert len(r['sources'])==3;assert r['common_include_lines']==[5]
@pytest.mark.parametrize('name',['formats','copies','common'])
def test_wrong_source(source,name):
 with pytest.raises(ValueError,match='frozen'):p.map_sources(dict(source,**{name:source[name]+b'!'}))
def test_missing(source):
 del source['common']
 with pytest.raises(ValueError,match='exact'):p.map_sources(source)
def test_duplicate_anchor(source,monkeypatch):
 source['formats']+=b'[[formats-size-compatibility]]\n';s=dict(p.SOURCES);s['formats']=(s['formats'][0],p.sha(source['formats']),s['formats'][2]);monkeypatch.setattr(p,'SOURCES',s)
 with pytest.raises(ValueError,match='anchor'):p.map_sources(source)
