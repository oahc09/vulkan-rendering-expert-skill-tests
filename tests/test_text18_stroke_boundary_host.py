import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).parent/'fixtures'
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ref=load(P/'text_stroke_boundary_lab/reference.py','boundary_ref')
old=load(P/'text_stroke_lab/run_lab.py','old_cases')
@pytest.mark.parametrize('xy',[(42.5,35.5),(39.5,36.5),(36.5,37.5)])
def test_closed_terminal_boundary(xy):
 c=old.CASES[3];assert ref.covered(c,*xy)
 assert ref.covered(dict(c,points=c['points'][::-1]),*xy)
def test_all_pixel_reversal_invariant():
 for c in old.CASES[3:]:
  reverse=dict(c,points=c['points'][::-1])
  assert all(ref.covered(c,x+.5,y+.5)==ref.covered(reverse,x+.5,y+.5) for y in range(49) for x in range(65))
def test_original_case_positions_not_changed():
 assert old.CASES[3]['points']==[(12.25,30.25),(32.25,12.25),(40.25,36.25)]
