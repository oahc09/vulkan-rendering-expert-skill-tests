import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/scene_b_shared_world_lab/run_lab.py'
s=importlib.util.spec_from_file_location('scene_b_reference',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_source_prism_ray_cap_and_side():
 poly=[(0,0),(2,0),(2,2),(0,2)]
 assert m.hit(poly,1,1,.25,.125)==(0,'cap')
 assert m.hit(poly,3,1,.25,0)==(4,'side')
 assert m.hit(poly,20,20,.25,.125) is None

def test_frozen_two_projection_ray_directions_differ():
 a=(.25,.125);b=(-.25,.25)
 assert a!=b
 for k,l in (a,b):
  for z in (0,1,3,6,10):
   world=(35,20,z);screen=(world[0]+k*z,world[1]+l*z)
   assert (screen[0]-k*z,screen[1]-l*z)==world[:2]
