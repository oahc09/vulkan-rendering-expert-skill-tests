import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
p=Path(__file__).parent/'fixtures/scene_b_vector_overlay_lab/geometry.py';s=importlib.util.spec_from_file_location('vector_panel',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_frozen_observable_regions():
 assert m.preflight()==dict(negative_1=36,negative_2=91,negative_3=35,negative_4=256,negative_5=12,path_only=297,stroke_only=68,hole_kept=256)
def test_rules_differ_on_same_direction_inner():
 for y in range(49):
  for x in range(65):
   p=(x+.5,y+.5)
   assert m.covered(p,0)==m.covered(p,6)==m.covered(p,8)
 assert sum(m.covered((x+.5,y+.5),7)!=m.covered((x+.5,y+.5),6) for y in range(49) for x in range(65))==256

def test_closed_rotated_clip_finite_segment_boundary():
 for p in [(28.5,11.5),(31.5,12.5),(34.5,13.5),(37.5,14.5),(40.5,15.5),(18,8),(48,18)]:assert m.closed_polygon(p,m.ROTATED)
 for p in [(15,7),(51,19)]:assert not m.closed_polygon(p,m.ROTATED)
