import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
HERE=Path(__file__).parent/'fixtures/text_fallback_lab'
def load(name):
 s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_whole_run_candidate_selection():
 m=load('run_lab');seen=[]
 class Fake:
  def shape(self,path,text,**kwargs):
   seen.append((path,text,kwargs));return {'missing_glyphs':int(path=='first'),'glyphs':[{'id':1}]}
 key,_,attempts=m.fallback(Fake(),'سلام','rtl','ar',{'primary':'first','secondary':'second'})
 assert key=='secondary' and [r[1] for r in seen]==['سلام','سلام']
 assert all(r[2]['direction']=='rtl' and r[2]['language']=='ar' for r in seen)
 assert [r['missing'] for r in attempts]==[1,0]
def test_complete_chain_failure():
 m=load('run_lab')
 class Fake:
  def shape(self,*args,**kwargs):return {'missing_glyphs':1,'glyphs':[{'id':0}]}
 with pytest.raises(ValueError,match='^no fallback face covers complete run$'):m.fallback(Fake(),'x','ltr','en',{'a':'a','b':'b'})
def test_untrusted_bytes_rejected_before_parsing(tmp_path):
 a=load('adapter');p=tmp_path/'bad';p.write_bytes(b'bad')
 with pytest.raises(ValueError,match='fixed trusted face mismatch before parsing'):a.shape(p,'x')
@pytest.mark.parametrize('field,value',[('font_sha256','wrong'),('face_index',2)])
def test_cross_face_receipt_rejected_before_raster(field,value):
 m=load('run_lab');a=load('adapter');r={'font_sha256':a.FACES['sans'][0],'face_index':0};r[field]=value
 with pytest.raises(ValueError,match='^shape face identity mismatch before raster$'):m.raster(a,'sans',r)
