import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/scene_a_board_lab/reference.py'
s=importlib.util.spec_from_file_location('board_reference',P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
@pytest.mark.parametrize('t',range(5))
def test_transform_inverse(t):
 for xy in [(8.25,12.5),(40.5,38.75),(32.5,24.5)]:assert r.transform(*r.transform(*xy,t),t,True)==pytest.approx(xy)
def test_nonzero_same_winding_overlapping_contours():
 square=[[(10,10),(12,10)],[(12,10),(12,12)],[(12,12),(10,12)],[(10,12),(10,10)]]
 cov=r.geometry([square,square],0)
 assert sum(cov)==4 and cov[10*65+10]==1
def test_fixed_rational_minification_is_original_inverse():
 import math
 for y in range(49):
  for x in range(65):
   u,v=r.transform(x+.5,y+.5,1,True)
   assert u-.5==pytest.approx((4*x-32)/3,abs=1e-13)
   assert v-.5==pytest.approx((4*y-24)/3,abs=1e-13)
   for n in (4*x-32,4*y-24):
    q=math.floor(n/3);rem=n-3*q
    assert 0<=rem<3 and q+rem/3==pytest.approx(n/3)
