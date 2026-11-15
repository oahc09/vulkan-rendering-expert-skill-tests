import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
p=Path(__file__).parent/'fixtures/scene_a_budget_board_lab/packing.py';s=importlib.util.spec_from_file_location('budgetpacking',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_actual_dimensions_include_header_and_padding():
 r=m.choose([(0,0,20,20),(0,0,10,10)],400000)
 assert r['payload_bytes']==r['width']*r['height']*16
 assert r['width']==80 and r['height']==121
 assert r['mode']==1
 assert m.choose([(0,0,20,20),(0,0,10,10)],20000)['mode']==0
 with pytest.raises(ValueError,match='cannot fit'):m.choose([(0,0,20,20)],10)
@pytest.mark.parametrize('budget',[True,-1,float('nan'),float('inf'),1.5])
def test_budget_rejected(budget):
 with pytest.raises(ValueError,match='invalid byte'):m.choose([(0,0,20,20)],budget)
def test_pack_rejects_count_and_length():
 p=m.choose([(0,0,20,20)],400000)
 with pytest.raises(ValueError,match='count'):m.pack(p,[])
 with pytest.raises(ValueError,match='length'):m.pack(p,[[0]])
def test_exact_reference_quantization_anchor():
 from fractions import Fraction as F
 exact=F(39,64)*F(61,64)*F(3,4)
 assert float(exact)==.43560791015625
 assert abs(.4482421875-float(exact))==.01263427734375
 assert abs(.3955078125-float(exact))==.04010009765625
def test_perspective_inverse_jacobian_and_positive_w():
 p=Path(__file__).parent/'fixtures/scene_a_budget_board_lab/board_reference.py';s=importlib.util.spec_from_file_location('projective_reference',p);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
 for x,y in [(0,0),(65,49),(32.5,24.5),(5.9375,24),(55.5,32)]:
  assert 1+(x-32.5)/128>0
  assert r.transform(*r.transform(x,y,6),6,True)==pytest.approx((x,y))
 for x,y in [(0,0),(32,32),(64,64)]:
  u,v=r.transform(x+.5,y+.5,6,True)
  assert u-.5==pytest.approx(96*x/(128-x))
  assert v-.5==pytest.approx((128*y-24*x-1024)/(128-x))
