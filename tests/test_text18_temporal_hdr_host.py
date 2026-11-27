import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
s=importlib.util.spec_from_file_location('temporal_ref',Path(__file__).parent/'fixtures/text_temporal_hdr_lab/run_lab.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_reset_discards_history():
 a=m.temporal_reference(0,[[0,.5,0,1]]*3185);b=m.temporal_reference(0,[[1,.5,0,1]]*3185)
 assert a==b and all(v[3]==0 for v in a)
def test_integer_pan_rejects_outside():
 history=[[v[0],.5,0,1] for v in m.temporal_reference(0,[[0,0,0,0]]*3185)]
 r=m.temporal_reference(1,history)
 assert all(r[y*65+64][3]==0 for y in range(49)) and sum(v[3]>0 for v in r)==64*49

def test_hdr_linear_domain():
 r=m.temporal_reference(0,[[0,0,0,0]]*3185)
 assert min(4*(.25+.75*v[0]) for v in r)>1
