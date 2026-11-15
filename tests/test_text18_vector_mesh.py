import pytest
from bounded_vector_mesh import triangulate,cross
pytestmark=pytest.mark.host_unit
P=[(8,8),(48,8),(48,40),(36,40),(36,20),(20,20),(20,40),(8,40)]
def path(points=P):return [('M',*points[0])]+[('L',*p) for p in points[1:]]+[('Z',)]
@pytest.mark.parametrize('transform',[(1,0,0,1,0,0),(-1,0,0,1,64,0),(1.5,0,0,.5,0,0)])
def test_concave_area_and_indices(transform):
 p,t=triangulate([path()],transform=transform)
 assert len(t)==len(p)-2 and all(len(set(q))==3 and all(0<=i<len(p) for i in q) for q in t)
 assert abs(sum(abs(cross(*(p[i] for i in q)))/2 for q in t)-960*abs(transform[0]*transform[3]))<1e-7
@pytest.mark.parametrize('paths',[[path(),path([(24,10),(28,10),(28,14),(24,14)])],[path([(0,0),(4,4),(0,4),(4,0)])],[path([(0,0),(1,0),(2,0)])]])
def test_reject_unsupported_topology(paths):
 with pytest.raises(ValueError):triangulate(paths)
