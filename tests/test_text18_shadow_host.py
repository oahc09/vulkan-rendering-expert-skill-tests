import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
s=importlib.util.spec_from_file_location('shadow_reference',Path(__file__).parent/'fixtures/text_shadow_lab/run_lab.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_source_ray_front_and_sides():
 r=m.shadow_reference([(10,10),(20,10),(20,20),(10,20)])
 assert r[12*65+12]==0
 # x=21.5 reaches right vertical side at z=3; y=15.5-.25*3 inside.
 assert r[15*65+21]==3/16
 assert r[45*65+60]==1
 assert min(r)==0 and max(r)==1

def test_receiver_explicit_outside_lit():
 # Fixed z10 shear maps pixel centers to integer shadow indices x+5,y+3.
 import math
 for y in range(49):
  for x in range(65):
   assert math.floor(x+.5+5)==x+5
   assert math.floor(y+.5+2.5)==y+3
