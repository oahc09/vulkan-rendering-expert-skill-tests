"""CPU path fallback tests, not Vulkan geometry/typography qualification."""
import math
import pytest
from bounded_vector_mask import flatten,coverage
pytestmark=pytest.mark.host_unit

def rect(x0,y0,x1,y1,reverse=False):
    p=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    if reverse:p.reverse()
    return [('M',*p[0])]+[('L',*q) for q in p[1:]]+[('Z',)]

@pytest.mark.parametrize('fill,reverse,hole',[('evenodd',False,True),('evenodd',True,True),('nonzero',False,False),('nonzero',True,True)])
def test_holes_and_winding(fill,reverse,hole):
    m=coverage([rect(1,1,7,7),rect(3,3,5,5,reverse)],8,8,fill=fill)
    assert m[4*8+4]==(0 if hole else 1)
    assert sum(m)==(32 if hole else 36)

def test_negative_scale_preserves_hole():
    paths=[rect(1,1,7,7),rect(3,3,5,5,True)]
    assert coverage(paths,8,8)==coverage(paths,8,8,transform=(-1,0,0,1,8,0))

def test_fractional_rect_area_reference():
    m=coverage([rect(.25,.5,4.75,5.5)],6,6)
    assert sum(m)==22.5 and any(0<v<1 for v in m)

@pytest.mark.parametrize('op,controls',[('Q',(0,8,8,0)),('C',(0,8,8,8,8,0))])
def test_curve_screen_error_against_dense_polynomial(op,controls):
    path=[('M',0,0),(op,*controls),('L',8,-2),('L',0,-2),('Z',)]
    poly=flatten([path],tolerance=.125)[0]
    def distance(p,a,b):
        dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
        return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
    for i in range(1001):
        t=i/1000
        p=(8*t*t,16*(1-t)*t) if op=='Q' else (24*(1-t)*t*t+8*t**3,24*(1-t)*t)
        assert min(distance(p,a,b) for a,b in zip(poly,poly[1:]))<=.125

@pytest.mark.parametrize('paths,options',[
    ([[('M',0,0),('L',4,4),('L',0,4),('L',4,0),('Z',)]],{}),
    ([rect(0,0,4,4),rect(4,1,6,3)],{}),
    ([rect(0,0,4,4)],{'transform':(0,0,0,1,0,0)}),
    ([[('M',0,0),('L',float('nan'),0),('Z',)]],{}),
    ([[('M',0,0),('L',0,0),('Z',)]],{}),
    ([[('M',0,0),('Q',0,10,10,0),('L',0,-1),('Z',)]],{'max_depth':1}),
    ([rect(0,0,4,4)],{'max_segments':3}),
    ([[('M',0,0),('A',1,2)]],{}),
])
def test_unsupported_or_budget_rejected(paths,options):
    with pytest.raises(ValueError):flatten(paths,**options)

def test_work_budget_and_fill_rejected():
    with pytest.raises(ValueError):coverage([rect(0,0,4,4)],8,8,max_work=2)
    with pytest.raises(ValueError):coverage([rect(0,0,4,4)],8,8,fill='guess')

def test_adjacent_backtracking_and_invalid_work_budget():
    path=[('M',0,0),('L',4,0),('L',2,0),('L',2,4),('L',0,4),('Z',)]
    with pytest.raises(ValueError):flatten([path])
    with pytest.raises(ValueError):coverage([rect(0,0,4,4)],8,8,max_work=float('nan'))
