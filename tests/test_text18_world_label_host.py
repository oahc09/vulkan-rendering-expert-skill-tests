import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/text_world_label_lab/run_lab.py'
s=importlib.util.spec_from_file_location('world_host',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_center_ray_maps_original_glyph_not_packed_coordinates():
 g={'size':[14,15],'pixels':[i/210 for i in range(210)]}
 cov,occ,t=m.sample(g,m.CASES[0],32,24)
 assert t==2.75 and cov==90/210 and not occ

def test_finite_plane_keeps_all_corners_in_registered_frustum():
 for c in m.CASES:
  depths=[c['z']+.25*x for x in (m.X0,m.X1)]
  assert min(depths)>1.125 and max(depths)<9

def test_world_extent_projects_smaller_at_second_distance():
 def width(z):return 32.5*(m.X1/(z+.25*m.X1)-m.X0/(z+.25*m.X0))
 assert width(2.75)>width(3.75)>0
