import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from tools import normative_prose19 as p
@pytest.fixture
def fixture(monkeypatch):
 raw=(''.join('[['+a+']]\nsection\nifdef::A[]\ntext\nendif::A[]\n' for a in p.ANCHORS)+'[[end]]\nother\n').encode()
 monkeypatch.setattr(p,'SHA256',p.sha(raw));return raw

def test_exact_slices(fixture):
 r=p.extract(fixture);assert len(r['slices'])==len(p.ANCHORS)
 lines=fixture.decode().splitlines(keepends=True)
 for row in r['slices']:
  assert row['raw_slice_sha256']==p.sha(''.join(lines[row['line_start']-1:row['line_end']]).encode())
  assert row['conditional_directives']==['ifdef::A[]','endif::A[]']
 assert r['status']=='EXACT_RAW_PROSE_SLICE_MAP'

@pytest.mark.parametrize('suffix',[b' ',b'\n',b'bad'])
def test_wrong_source(fixture,suffix):
 with pytest.raises(ValueError,match='frozen'):p.extract(fixture+suffix)

@pytest.mark.parametrize('duplicate',[True,False])
def test_anchor_integrity(fixture,monkeypatch,duplicate):
 raw=fixture+(('[['+p.ANCHORS[0]+']]\n').encode()) if duplicate else fixture.replace(p.ANCHORS[0].encode(),b'renamed')
 monkeypatch.setattr(p,'SHA256',p.sha(raw))
 with pytest.raises(ValueError,match='anchor'):p.extract(raw)
