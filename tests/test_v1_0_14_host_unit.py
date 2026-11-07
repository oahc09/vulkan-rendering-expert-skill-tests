"""Deterministic CPU contracts only, not GPU/visual acceptance."""
import pytest
from visual_host_contracts import *
pytestmark=pytest.mark.host_unit

def test_history_events_and_view_isolation():
    a=HistoryKey(1,1,1,64,64)
    assert history_policy(a,a,'none')=='keep'
    for event in ['camera_cut','pause_resume','device_recreate','effect_switch']:
        assert history_policy(a,a,event)=='reset'
    for b in [HistoryKey(2,1,1,64,64),HistoryKey(1,2,1,64,64),HistoryKey(1,1,2,64,64)]:
        assert history_policy(a,b,'none',resampling_supported=True)=='reset'
    b=HistoryKey(1,1,1,32,32)
    assert history_policy(a,b,'none')=='reset'
    assert history_policy(a,b,'none',resampling_supported=True)=='resample'
    for e in ['material','geometry','light']:assert history_policy(a,a,e)=='reject_affected'
    assert history_policy(a,HistoryKey(1,1,1,0,0),'none')=='suspend'

def test_motion_direction_units_and_single_jitter_removal():
    assert reproject((.5,.5),(1,0),(100,100))==(.51,.5)
    assert reproject((.5,.5),(.01,0),(100,100),units='uv')==(.51,.5)
    with pytest.raises(ValueError):reproject((.5,.5),(-.01,0),(100,100),units='uv',direction='previous_to_current')
    assert reproject((.5,.5),(1.5,0),(100,100),includes_jitter=True,previous_jitter=(.5,0))==(.51,.5)
    with pytest.raises(ValueError):reproject((0,0),(1,1),(0,1))
    with pytest.raises(ValueError):reproject((0,0),(1,1),(1,1),units='unknown')

@pytest.mark.parametrize('valid,depth,normal',[(False,0,1),(True,.1,1),(True,0,.1)])
def test_disocclusion_and_edges_reject_history(valid,depth,normal):
    out,w=temporal_sample(0,1,valid=valid,depth_delta=depth,normal_dot=normal,confidence=.9)
    assert out==w==0

def test_exposure_radiance_is_not_visibility():
    out,w=temporal_sample(4,2,valid=True,depth_delta=0,normal_dot=1,confidence=.9,previous_exposure=1,current_exposure=2,signal='radiance',neighborhood=(0,8))
    assert out==4 and w==.9
    assert temporal_sample(2,2,valid=True,depth_delta=0,normal_dot=1,confidence=0)[0]==1
    with pytest.raises(ValueError):temporal_sample(1,1,valid=True,depth_delta=0,normal_dot=1,confidence=1,previous_exposure=0)

def test_scratch_checks_addresses_not_just_offsets():
    assert scratch_ranges_valid([(256,256),(512,256)],256)
    assert not scratch_ranges_valid([(256,512),(512,256)],256)
    assert scratch_ranges_valid([(256,512),(512,256)],256,serialized=True)
    assert not scratch_ranges_valid([(257,256)],256,serialized=True)
    assert not scratch_ranges_valid([(2**64-256,512)],256)

def test_as_update_and_retirement_are_separate():
    assert as_update_allowed(original_allow_update=True,old_signature=('tri',3),new_signature=('tri',3))
    assert not as_update_allowed(original_allow_update=False,old_signature=('tri',3),new_signature=('tri',3))
    assert not as_update_allowed(original_allow_update=True,old_signature=('tri',3),new_signature=('tri',4))
    for complete,tl,sh in [(False,0,0),(True,1,0),(True,0,1)]:assert not can_retire(submitted=True,completed=complete,tlas_references=tl,shading_references=sh)
    assert can_retire(submitted=True,completed=True,tlas_references=0,shading_references=0)

def test_omm_material_changes_and_unknown_are_not_transparent():
    for supported,key,opacity in [(False,'a','opaque'),(True,'b','opaque'),(True,None,'opaque')]:
        assert omm_action(supported=supported,bake_key='a',material_key=key,opacity=opacity)=='disable_or_rebuild_then_material_test'
    assert omm_action(supported=True,bake_key=None,material_key=None,opacity='opaque')=='disable_or_rebuild_then_material_test'
    assert omm_action(supported=True,bake_key='a',material_key='a',opacity='unknown')=='material_test'
    assert omm_action(supported=True,bake_key='a',material_key='a',opacity='transparent')=='continue'

def test_budget_hysteresis_and_capability_fallback():
    c=TierController()
    assert c.step(pressure=True,supported=True)==0
    for _ in range(5):assert c.step(pressure=False,supported=True)==0
    assert c.step(pressure=False,supported=True)==1
    assert c.step(pressure=False,supported=False)==0


@pytest.mark.parametrize('size',[(float('nan'),100),(float('inf'),100),(1.5,100),(True,100)])
def test_invalid_dimensions_do_not_silently_corrupt_motion(size):
    with pytest.raises(ValueError):reproject((.5,.5),(1,0),size)

@pytest.mark.parametrize('uv,mv,jitter',[((.5,), (1,0),(0,0)),((.5,.5),(1,),(0,0)),((.5,.5),(1,0),(0,))])
def test_motion_vectors_require_two_components(uv,mv,jitter):
    with pytest.raises(ValueError):reproject(uv,mv,(100,100),current_jitter=jitter)

def test_hdr_neighborhood_is_mandatory_and_exposure_overflow_rejected():
    args=dict(valid=True,depth_delta=0,normal_dot=1,confidence=.9,signal='radiance')
    with pytest.raises(ValueError):temporal_sample(4,4,**args)
    assert temporal_sample(4,4,neighborhood=(0,8),**args)[0]==4
    with pytest.raises(ValueError):temporal_sample(4,0,previous_exposure=1e-308,current_exposure=1e308,neighborhood=(0,8),**args)


def test_invalid_previous_history_never_resamples():
    assert history_policy(HistoryKey(1,1,1,0,0),HistoryKey(1,1,1,100,100),'resize',resampling_supported=True)=='reset'
