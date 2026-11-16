import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from tools import layout_prose19 as p
@pytest.fixture
def source(monkeypatch):
 a=(''.join('[['+x+']]\ntext\n' for x in p.ANCHORS)+'include::{chapters}/commonvalidity/push_constants_common.adoc[]\n').encode();b=b'common'
 monkeypatch.setattr(p,'CHAPTER_SHA',p.sha(a));monkeypatch.setattr(p,'COMMON_SHA',p.sha(b));return a,b

def test_map(source):
 r=p.map_sources(*source);assert len(r['chapter']['slices'])==3;assert r['resolved_common_include']['include_lines']==[7]
@pytest.mark.parametrize('index',[0,1])
def test_wrong_bytes(source,index):
 a=list(source);a[index]+=b'X'
 with pytest.raises(ValueError,match='frozen'):p.map_sources(*a)
def test_missing_include(source,monkeypatch):
 a=source[0].split(b'include::')[0];monkeypatch.setattr(p,'CHAPTER_SHA',p.sha(a))
 with pytest.raises(ValueError,match='include'):p.map_sources(a,source[1])
def test_duplicate_anchor(source,monkeypatch):
 a=source[0]+b'[[descriptors-compatibility]]\n';monkeypatch.setattr(p,'CHAPTER_SHA',p.sha(a))
 with pytest.raises(ValueError,match='anchor'):p.map_sources(a,source[1])
