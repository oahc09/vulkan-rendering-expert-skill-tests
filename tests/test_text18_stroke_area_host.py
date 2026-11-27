from fractions import Fraction as F
import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/text_stroke_area_lab'
def load(f,n):
 s=importlib.util.spec_from_file_location(n,P/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
ref=load('reference.py','area_reference_host');runner=load('run_lab.py','area_runner_host')
@pytest.mark.parametrize('c',runner.CASES,ids=lambda c:c['name'])
def test_exact_integral_conserves_registered_stroke_area(c):
 total=sum((ref.area(c,x,y) for y in range(49) for x in range(65)),F(0))
 length=20 if c['points'][1][1]==c['points'][0][1] else 25
 assert total==F(c['width'])*(length+(c['width'] if c['cap']=='square' else 0))
def test_fractional_corner_known_area():
 c=runner.CASES[0]
 assert ref.area(c,10,9)==F(3,16)
 assert ref.area(c,10,10)==F(3,4)
def test_unsupported_direction_rejected():
 with pytest.raises(ValueError,match='unsupported registered direction'):ref.polygon(dict(runner.CASES[0],points=[(10,10),(11,12)]))
