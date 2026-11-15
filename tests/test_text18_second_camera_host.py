import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/text_second_camera_lab/run_lab.py'
s=importlib.util.spec_from_file_location('camera_host',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_camera_b_is_orthonormal_and_rotated_not_distance_only():
 b=m.CAMERAS['B'];a=m.CAMERAS['A'];vectors=[b[k] for k in ('right','up','forward')]
 for i,u in enumerate(vectors):
  for j,v in enumerate(vectors):assert sum(x*y for x,y in zip(u,v))==pytest.approx(1 if i==j else 0,abs=1e-15)
 assert b['origin']!=a['origin'] and b['forward']!=a['forward']

def test_registered_view_translation_matches_camera_origin():
 b=m.CAMERAS['B'];o=b['origin'];assert [-sum(x*y for x,y in zip(b[k],o)) for k in ('right','up','forward')]==pytest.approx([-.41,-.125,.38])

def test_cpu_center_ray_intersects_original_world_plane():
 b=m.CAMERAS['B'];o=b['origin'];d=b['forward'];t=(2.75+.25*o[0]-o[2])/(d[2]-.25*d[0]);p=[o[i]+t*d[i] for i in range(3)]
 assert p[2]==pytest.approx(2.75+.25*p[0],abs=1e-14)
 assert 1<t<10
