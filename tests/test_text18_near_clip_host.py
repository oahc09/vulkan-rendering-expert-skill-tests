import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
P=Path(__file__).parent/'fixtures/text_near_clip_lab/run_lab.py'
s=importlib.util.spec_from_file_location('near_host',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
G={'size':[14,15],'pixels':[1.]*210}
def test_fixed_cross_plane_actually_straddles_near():
 c=m.CASES[0];assert c['z']+c['tilt']*m.X0==.375
 assert c['z']+c['tilt']*m.X1==1.5
 assert m.sample(G,c,32,24)[0]==0
 assert m.sample(G,c,48,24)[0]==1

def test_exact_near_boundary_is_included():
 cov,_,t=m.sample(G,m.CASES[1],32,24);assert t==1 and cov==1

def test_behind_near_is_positive_w_but_no_visible_glyph():
 c=m.CASES[2];assert 0<c['z']+c['tilt']*m.X0<c['z']+c['tilt']*m.X1<1
 assert all(m.sample(G,c,x,y)[0]==0 for y in range(49) for x in range(65))
