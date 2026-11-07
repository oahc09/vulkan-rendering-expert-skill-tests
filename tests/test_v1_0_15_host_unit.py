"""Deterministic semantic checks with tolerances fixed before Vulkan outputs."""
from dataclasses import replace
from math import exp
import pytest
from transparency_host_contracts import *
pytestmark=pytest.mark.host_unit
R=(1.,0.,0.,.5);B=(0.,0.,1.,.5)

def test_source_over_and_reverse_depth():
    assert accumulate([B,R])==(.5,0,.25,.75)
    assert accumulate([R,B])==(.25,0,.5,.75)
    assert transmittance_front_to_back([R,B])==accumulate([B,R])
    assert source_over((.5,0,0,.5),(.0,0,.5,.5))==(.5,0,.25,.75)
    assert source_over(R,(0,0,.5,.5),representation='straight')==(.5,0,.25,.75)
    assert source_over(R,(0,0,.5,.5))!=(.5,0,.25,.75) # detect accidental double/missing premultiplication

@pytest.mark.parametrize('fmt,tolerance',[('fp64',1e-12),('fp16',.015)])
def test_low_alpha_accumulation_and_storage_model(fmt,tolerance):
    layers=[(.8,.4,.2,.01)]*128
    out=accumulate(layers,fmt=fmt);a=1-.99**128
    assert max(abs(x-y) for x,y in zip(out,(.8*a,.4*a,.2*a,a)))<tolerance
    if fmt!='fp64':assert out!=accumulate(layers)

def test_rgba8_can_fail_declared_quality_budget_without_relaxing_it():
    layers=[(.8,.4,.2,.01)]*128
    out=accumulate(layers,fmt='rgba8'); reference=accumulate(layers)
    error=max(abs(x-y) for x,y in zip(out,reference))
    assert error>.13 # This quality tier fails; do not increase its tolerance.
    # Rounding perturbation recurrence: e_n <= .5/255 * sum((1-a)^i).
    numerical_bound=(.5/255)*(1-.99**128)/.01
    assert error<=numerical_bound


def test_input_quantization_is_not_attachment_error():
    exact=accumulate([(1,1,1,.001)]*128)
    quantized=accumulate([stored((1,1,1,.001),'rgba8')]*128)
    assert exact[3]>.1 and quantized==(0,0,0,0)
    with pytest.raises(ValueError):stored((1e9,0,0,1),'fp16')

def test_wboit_approximation_and_capability_fallback():
    assert wboit([R,B])==wboit([B,R])==(.375,0,.375,.75)
    assert wboit([R,B])!=accumulate([B,R])
    assert wboit([])==(0,0,0,0)
    assert select_transparency_path(independent_blend=True,accum_blend=True,reveal_blend=True)=='wboit_mrt'
    assert select_transparency_path(independent_blend=False,accum_blend=True,reveal_blend=True)=='sorted'
    assert select_transparency_path(independent_blend=False,accum_blend=True,reveal_blend=True,multipass_allowed=True)=='wboit_multipass'
    assert select_transparency_path(independent_blend=True,accum_blend=False,reveal_blend=True)=='sorted'

def test_capacity_overflow_and_stable_ties():
    f=[dict(depth=1,id=2),dict(depth=1,id=1)]
    assert [x['id'] for x in bounded_fragments(f,2,2)['fragments']]==[1,2]
    for cap,pool in [(1,2),(2,1),(0,0)]:
        r=bounded_fragments(f,cap,pool);assert r['status']=='overflow_rejected' and r['overflow']>0 and r['fragments']==[]
    with pytest.raises(ValueError):bounded_fragments(f,-1,10)

@pytest.mark.parametrize('step',[.25,.125,.03])
def test_volume_step_invariance(step):
    assert volume_transmittance(.7,2.,step)==pytest.approx(exp(-1.4),abs=1e-12)

def test_volume_invalid_and_soft_particle():
    for args in [(-1,1,.1),(1,1,0),(float('nan'),1,.1),(1,1,1e-9)]:
        with pytest.raises(ValueError):volume_transmittance(*args)
    assert soft_particle(2,2,.1)==0 and soft_particle(2,1.95,.1)==pytest.approx(.5)
    assert soft_particle(2,1,.1)==1

def test_explicit_profiles_normalize_equivalent_data():
    a=decode_gaussian((0,0,1),(1,1,1),.5,(1,0,0,0),(.5,.5,.5),profile=GaussianProfile('linear','probability','wxyz','linear_rgb'))
    b=decode_gaussian((0,0,1),(0,0,0),0,(0,0,0,1),(0,0,0),profile=GaussianProfile('log','logit','xyzw','sh_dc'))
    assert a==b
    for change in [dict(scale=(-1,1,1)),dict(opacity=2),dict(rotation=(0,0,0,0)),dict(position=(float('nan'),0,1)),dict(profile=None)]:
        args=dict(position=(0,0,1),scale=(1,1,1),opacity=.5,rotation=(1,0,0,0),color=(.5,.5,.5),profile=GaussianProfile('linear','probability','wxyz','linear_rgb'));args.update(change)
        with pytest.raises(ValueError):decode_gaussian(**args)

def test_covariance_and_footprint():
    assert covariance_valid((1,0,0,1,0,1))
    for c in [(0,0,0,1,0,1),(1,2,0,1,0,1),(float('nan'),0,0,1,0,1),(-1,0,0,-1,0,1)]:assert not covariance_valid(c)
    assert footprint_visible(-2,20,4,4,width=64,height=64,z=1,near=.1)=='visible'
    assert footprint_visible(-10,20,4,4,width=64,height=64,z=1,near=.1)=='culled'
    assert footprint_visible(0,20,4,4,width=64,height=64,z=.05,near=.1)=='near_plane_fallback'

def test_full_cache_invalidation_and_view_isolation():
    key=SortKey(1,1,(0.,0.,1.),(1,),0.,'a',(0,),(1,2),(1,),'stable_depth_id')
    assert sort_cache_valid(key,key)
    for name,value in [('engine',2),('view',2),('camera',(1.,0.,1.)),('transforms',(2,)),('time',1.),('parameters','b'),('lod',(1,)),('visible_ids',(1,)),('generations',(2,)),('index_policy','other')]:
        assert not sort_cache_valid(key,replace(key,**{name:value}))
    assert not sort_cache_valid(None,key)

def test_fewer_points_can_cost_more_coverage():
    many=coverage_estimate([(1,1)]*100,100);few=coverage_estimate([(3,3)]*50,50)
    assert few['count']<many['count'] and few['ellipse_area']>many['ellipse_area']
    assert 'not_hardware' in few['kind']

@pytest.mark.parametrize('value',[(0,0,0,float('nan')),(0,0,0,2),(0,0,float('inf'),.5)])
def test_invalid_alpha_and_colors_rejected(value):
    with pytest.raises(ValueError):source_over(value,(0,0,0,0))


@pytest.mark.parametrize('fragments',[[dict(depth=float('nan'),id=1)],[dict(depth=1,id=-1)],[dict(depth=1,id=1),dict(depth=2,id=1)]])
def test_invalid_fragment_records_rejected(fragments):
    with pytest.raises(ValueError):bounded_fragments(fragments,8,8)


def test_finite_inputs_cannot_silently_overflow_oracle():
    with pytest.raises(ValueError):wboit([(1e308,0,0,1.)]*2)
    with pytest.raises(ValueError):source_over((1.3e308,0,0,.5),(1.3e308,0,0,.5))
    with pytest.raises(ValueError):volume_transmittance(1.,1e308,1e-308)
