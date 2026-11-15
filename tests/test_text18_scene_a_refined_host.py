import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/scene_a_refined_board_lab/reference.py'
s=importlib.util.spec_from_file_location('refined_ref',P);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
@pytest.mark.parametrize('t',range(6))
def test_common_square_transform_inverse(t):
 for p in [(5.9375,24),(55.5,32),(32.5,24.5)]:assert r.transform(*r.transform(*p,t),t,True)==pytest.approx(p)
def test_exact_thin_stem_anchor():
 c=[[(24.5,22.75),(25.3125,22.75)],[(25.3125,22.75),(25.3125,32)],[(25.3125,32),(24.5,32)],[(24.5,32),(24.5,22.75)]]
 g=r.geometry([c],4)
 assert g[31*65+25]==.8125
 assert g[31*65+25]*.75==.609375
 assert min(26,25.3125+.5)-max(25,24.5+.5)==.8125
