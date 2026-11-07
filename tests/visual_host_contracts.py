"""Original CPU reference policies, not Vulkan execution or device evidence."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class HistoryKey:
    engine: int
    view: int
    generation: int
    width: int
    height: int

def history_policy(previous, current, event, *, resampling_supported=False):
    if min(current.width,current.height)<=0:
        return 'suspend'
    if previous is None or min(previous.width,previous.height)<=0 or (previous.engine,previous.view,previous.generation)!=(current.engine,current.view,current.generation):
        return 'reset'
    if event in {'camera_cut','device_recreate','pause_resume','effect_switch'}:
        return 'reset'
    if (previous.width,previous.height)!=(current.width,current.height) or event in {'viewport','projection','render_scale'}:
        return 'resample' if resampling_supported else 'reset'
    if event in {'material','geometry','light'}:
        return 'reject_affected'
    return 'keep'

def reproject(uv, motion, size, *, direction='current_to_previous', units='pixel', includes_jitter=False, current_jitter=(0.,0.), previous_jitter=(0.,0.)):
    if direction not in {'current_to_previous','previous_to_current'} or units not in {'pixel','uv'}:
        raise ValueError('Explicit direction/units required')
    if (any(len(v)!=2 for v in (uv,motion,size,current_jitter,previous_jitter))
            or any(isinstance(x,bool) or not isinstance(x,int) or x<=0 for x in size)
            or not all(isfinite(x) for x in (*uv,*motion,*current_jitter,*previous_jitter))):
        raise ValueError('Invalid motion contract')
    if direction=='previous_to_current':
        raise ValueError('Forward MV needs inverse correspondence/resampling, not sign flip')
    scale=1
    delta=[scale*motion[i]/(size[i] if units=='pixel' else 1) for i in range(2)]
    # Current/previous UV in this reference are unjittered, jitter is in pixels.
    if includes_jitter:
        delta=[delta[i]-(previous_jitter[i]-current_jitter[i])/size[i] for i in range(2)]
    return tuple(uv[i]+delta[i] for i in range(2))

def temporal_sample(current, history, *, valid, depth_delta, normal_dot, confidence, previous_exposure=1., current_exposure=1., signal='visibility', neighborhood=None):
    if signal not in {'visibility','radiance'}:
        raise ValueError('Unknown signal')
    if neighborhood is None:
        if signal=='radiance':raise ValueError('Radiance requires explicit HDR neighborhood bounds')
        neighborhood=(0.,1.)
    if len(neighborhood)!=2:raise ValueError('Expected lower/upper bounds')
    if not all(isfinite(x) for x in (current,history,depth_delta,normal_dot,confidence,previous_exposure,current_exposure,*neighborhood)):
        raise ValueError('Non-finite input')
    if previous_exposure<=0 or current_exposure<=0 or neighborhood[0]>neighborhood[1]:
        raise ValueError('Invalid exposure/neighborhood')
    weight=min(.9,max(0.,confidence)) if valid and abs(depth_delta)<=.02 and normal_dot>=.9 else 0.
    if signal=='radiance':
        ratio=current_exposure/previous_exposure
        if not isfinite(ratio) or not isfinite(history*ratio):
            raise ValueError('Invalid exposure conversion; reset history')
        history*=ratio
    history=max(neighborhood[0],min(neighborhood[1],history))
    out=current*(1-weight)+history*weight
    if not isfinite(out):raise ValueError('Non-finite temporal result')
    return (max(0.,min(1.,out)) if signal=='visibility' else out),weight

def scratch_ranges_valid(ranges, alignment, *, serialized=False):
    if alignment<=0 or alignment&(alignment-1):
        raise ValueError('Alignment must be positive power of two')
    if any(addr<0 or size<=0 or addr%alignment or addr+size>2**64 for addr,size in ranges):
        return False
    return serialized or all(a+s<=b or b+t<=a for i,(a,s) in enumerate(ranges) for b,t in ranges[i+1:])

def as_update_allowed(*, original_allow_update, old_signature, new_signature):
    # Signature must include ALL relevant target-spec invariants, not just topology.
    return bool(original_allow_update and old_signature and old_signature==new_signature)

def can_retire(*, submitted, completed, tlas_references, shading_references):
    if min(tlas_references,shading_references)<0:raise ValueError('Negative references')
    return (not submitted or completed) and tlas_references==shading_references==0

def omm_action(*, supported, bake_key, material_key, opacity):
    if opacity not in {'opaque','transparent','unknown'}:raise ValueError('Invalid opacity')
    if not supported or not bake_key or not material_key or bake_key!=material_key:
        return 'disable_or_rebuild_then_material_test'
    return {'opaque':'confirm','transparent':'continue','unknown':'material_test'}[opacity]

@dataclass
class TierController:
    tier: int=1
    stable_frames: int=0
    cooldown: int=0
    def step(self, *, pressure, supported, restore_after=3):
        if restore_after<1:raise ValueError('Invalid hysteresis')
        if not supported or pressure:
            self.tier=0;self.cooldown=restore_after;self.stable_frames=0
        elif self.cooldown:
            self.cooldown-=1
        else:
            self.stable_frames+=1
            if self.stable_frames>=restore_after:self.tier=1
        return self.tier
