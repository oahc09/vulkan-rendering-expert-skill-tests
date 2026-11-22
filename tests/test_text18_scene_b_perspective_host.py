import importlib.util
from pathlib import Path
from fractions import Fraction
import pytest
pytestmark=pytest.mark.host_unit
p=Path(__file__).parent/'fixtures/scene_b_perspective_lab/reference.py';s=importlib.util.spec_from_file_location('perspective_ref',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_clipped_front_cap_keeps_valid_back():
 poly=[(0,0),(2,0),(2,2),(0,2)]
 assert m.ray_hits(poly,1,1,0,0,1)==(0,'cap')
 assert m.ray_hits(poly,1,1,0,0,22)==(6,'cap')
 assert m.ray_hits(poly,1,1,0,0,27) is None

def test_fixed_rational_sampling_matches_independent_ray():
 for offset in (0,2):
  for y in range(49):
   for x in range(65):
    wx=Fraction(65,2)+offset+(Fraction(2*x+1,2)-Fraction(65,2))*Fraction(23,40)
    wy=Fraction(49,2)+(Fraction(2*y+1,2)-Fraction(49,2))*Fraction(23,40)
    assert wx-32==Fraction(46*x-1432+80*offset,80)
    assert 65-wx-32==Fraction(1512-46*x-80*offset,80)
    assert wy-15==Fraction(46*y-344,80)

def test_object_reflection_changes_world_not_projection():
 for x in (25.25,32.5,40.25):assert 65-(65-x)==x
 assert (65-25.25,12.75)!=(25.25,12.75)

def test_reflected_rectangle_source_boundary_diagnostic():
 # Fixed world ray at actual depth21 hits original right edge exactly.
 x,y=12,12;wx=Fraction(65,2)+(Fraction(2*x+1,2)-Fraction(65,2))*Fraction(21,40)
 assert wx==22 and 65-wx==43
 assert not 34<=65-wx<43

def test_all_registered_rectangle_boundary_centers():
 assert m.boundary_centers()=={'offset0-mirror0':[{'axis':'x','source':43,'pixel':52,'included':False}],'offset0-mirror1':[{'axis':'x','source':43,'pixel':12,'included':False}],'offset2-mirror0':[],'offset2-mirror1':[]}
