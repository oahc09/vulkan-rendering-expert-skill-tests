"""CPU contract boundaries; independent of the opt-in Vulkan sweep."""
import importlib.util
import math
from pathlib import Path
import pytest
pytestmark = pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/text_stroke_lab'
s=importlib.util.spec_from_file_location('stroke_host',P/'stroke.py');stroke=importlib.util.module_from_spec(s);s.loader.exec_module(stroke)

def test_miter_limit_inclusive_boundary():
 points=[(12.25,30.25),(32.25,12.25),(40.25,36.25)]
 _,r=stroke.generate(points,8,join='miter',miter_limit=3)
 ratio=r['miter_ratio']
 assert stroke.generate(points,8,join='miter',miter_limit=ratio)[1]['effective_join']=='miter'
 assert stroke.generate(points,8,join='miter',miter_limit=math.nextafter(ratio,0))[1]['effective_join']=='bevel'

@pytest.mark.parametrize('points,reason',[([(10,10),(10,10)],'zero segment'), ([(10,10),(20,10),(10,10)],'reversal unsupported')])
def test_degenerate_rejected(points,reason):
 with pytest.raises(ValueError,match=reason):stroke.generate(points,4)

def test_round_triangle_budget_exact():
 assert len(stroke.generate([(10,10),(20,10)],6,cap='round',max_triangles=130)[0])==130
 with pytest.raises(ValueError,match='triangle budget'):stroke.generate([(10,10),(20,10)],6,cap='round',max_triangles=129)

def test_cap_output_boundary():
 assert stroke.generate([(3,10),(20,10)],6,cap='round')
 with pytest.raises(ValueError,match='output bounds'):stroke.generate([(2.99,10),(20,10)],6,cap='round')

def test_registered_guard_covers_sagitta_and_reserve():
 s=importlib.util.spec_from_file_location('stroke_runner_host',P/'run_lab.py');runner=importlib.util.module_from_spec(s);s.loader.exec_module(runner)
 assert 4*(1-math.cos(math.pi/stroke.CAP_STEPS))+.005<=runner.GUARD
