"""Numerical and state host evidence only; no fabricated shader/device output."""
import math
import pytest
from simulation_host_contracts import Clock,integrate,distance,lambda_policy,solve,plane,sphere,capsule,wave,Snapshot,Snapshots
pytestmark=pytest.mark.host_unit

@pytest.mark.parametrize('fps',[30,60,120])
def test_clock_equal_ticks_and_once_events_multiview(fps):
    clock=Clock();clock.enqueue('click',.25,3.)
    assert not clock.enqueue('click',.25,3.)
    events=[]
    for frame in range(fps):
        events.extend(e for _,batch in clock.advance(frame,1/fps) for e in batch)
        assert clock.advance(frame,1/fps)==[]
    assert clock.tick==60 and events==[('click',3.)]
    assert clock.accumulator==pytest.approx(0,abs=1e-12)
    assert not clock.enqueue('click',.25,3.)


def test_clock_pause_and_bounded_backlog():
    c=Clock();c.paused=True
    assert c.advance(0,40)==[] and c.tick==0 and c.dropped_time==40
    c.paused=False
    assert len(c.advance(1,1/60))==1
    assert len(c.advance(2,10))==4
    assert c.dropped_time==pytest.approx(40+10-4/60)
    assert c.accumulator< c.step
    with pytest.raises(ValueError):c.advance(1,0)

@pytest.mark.parametrize('dt',[-1,math.inf,math.nan])
def test_clock_invalid_dt_does_not_mutate(dt):
    c=Clock()
    with pytest.raises(ValueError):c.advance(0,dt)
    assert c.tick==0 and c.last_frame==-1


def test_bounded_input_overflow_is_observable():
    c=Clock(capacity=1)
    assert c.enqueue('one',0,1)
    assert not c.enqueue('two',0,1) and c.overflow==1
    assert c.advance(0,1/60)==[(1,[('one',1)])]


def test_force_integrated_impulse_once_and_fixed_point():
    for steps in [1,4,16]:
        x=(0.,0.,0.);v=x
        for i in range(steps): x,v=integrate(x,v,1.,(2.,0.,0.),(3.,0.,0.) if i==0 else (0.,0.,0.),1/steps)
        assert v==(5.,0.,0.)
    assert integrate((1,0,0),(0,0,0),0,(5,0,0),(3,0,0),.1)==((1,0,0),(0,0,0))

@pytest.mark.parametrize('alpha,expected,lam',[(0.,1.,-.2),(.01,1.1,-.1)])
def test_xpbd_hard_soft_pregistered_oracle(alpha,expected,lam):
    a,b,l=distance((0,0,0),(1.2,0,0),0,1,1,alpha,.1)
    assert a==(0,0,0)
    assert b==pytest.approx((expected,0,0),abs=1e-12)
    assert l==pytest.approx(lam,abs=1e-12)


def test_lambda_lifetime_and_actual_substep_h():
    a,b,l=distance((0,0,0),(1.2,0,0),0,1,1,.01,.1)
    _,retained,ll=distance(a,b,0,1,1,.01,.1,l)
    _,wrong,_=distance(a,b,0,1,1,.01,.1,0)
    assert retained==pytest.approx(b,abs=1e-12) and ll==pytest.approx(l,abs=1e-12)
    assert wrong[0]==pytest.approx(1.05)
    assert distance(a,(1.2,0,0),0,1,1,.01,.05)[1][0]==pytest.approx(1.16)
    # key: world, topology, material, h, integration substep
    key=(1,2,.01,.1,4)
    assert lambda_policy(key,key)=='retain'
    for changed in [(2,2,.01,.1,4),(1,3,.01,.1,4),(1,2,.02,.1,4),(1,2,.01,.05,4),(1,2,.01,.1,5)]:
        assert lambda_policy(key,changed)=='reset'

@pytest.mark.parametrize('wa,wb,rest,alpha,h', [(-1,1,1,0,.1),(0,1,-1,0,.1),(0,1,1,-1,.1),(0,1,1,0,0),(0,1,1,0,float('nan'))])
def test_invalid_xpbd_parameters(wa,wb,rest,alpha,h):
    with pytest.raises(ValueError):distance((0,0,0),(1,0,0),wa,wb,rest,alpha,h)


def test_degenerate_fixed_and_duplicate_constraints():
    assert distance((0,0,0),(0,0,0),1,1,1,0,.1)==((0,0,0),(0,0,0),0)
    assert distance((0,0,0),(2,0,0),0,0,1,0,.1)==((0,0,0),(2,0,0),0)
    with pytest.raises(ValueError):solve([(0,0,0),(2,0,0)],[0,1],[(0,1,1,0)]*2,.1,1,colors=[[0,1]])


def test_colored_and_jacobi_same_two_particle_reference():
    for colors in (None,[[0]]):
        x,l=solve([(0,0,0),(1.2,0,0)],[0,1],[(0,1,1,.01)],.1,8,colors=colors)
        assert x[1][0]==pytest.approx(1.1,abs=1e-12) and l[0]==pytest.approx(-.1,abs=1e-12)


def test_jacobi_gather_matches_frozen_input_contributions_not_gauss_seidel():
    x=[(0,0,0),(1.1,0,0),(2.2,0,0)];edges=[(0,1,1,0),(1,2,1,0)]
    out,_=solve(x,[0,1,1],edges,.1,1)
    assert [p[0] for p in out]==pytest.approx([0,1.05,2.15],abs=1e-12)
    gs,_=solve(x,[0,1,1],edges,.1,1,colors=[[0],[1]])
    assert [p[0] for p in gs]==pytest.approx([0,1.1,2.1],abs=1e-12)
    # Controlled low-valence short chain only, not universal Jacobi stability.
    refined,_=solve(x,[0,1,1],edges,.1,40)
    assert abs(refined[2][0]-2)<1e-6


def test_color_write_sets_topology_and_fixed_sharing():
    x=[(0,0,0),(1.1,0,0),(-1.1,0,0)]
    edges=[(0,1,1,0),(0,2,1,0)]
    assert solve(x,[0,1,1],edges,.1,1,colors=[[0,1]])[0][1][0]==pytest.approx(1.)
    with pytest.raises(ValueError):solve(x,[1,1,1],edges,.1,1,colors=[[0,1]])
    for colors in ([[0]],[[0],[0,1]]):
        with pytest.raises(ValueError):solve(x,[0,1,1],edges,.1,1,colors=colors)


def test_plane_sphere_capsule_projection_and_degeneracy():
    assert plane((1,-2,3),(0,2,0),0)==(1,0,3)
    assert plane((1,2,3),(0,1,0),0)==(1,2,3)
    assert sphere((.5,0,0),(0,0,0),1)==(1,0,0)
    assert sphere((0,0,0),(0,0,0),1)==(1,0,0)
    assert sphere((2,0,0),(0,0,0),1)==(2,0,0)
    assert capsule((.2,1,0),(0,0,0),(0,2,0),1)==(1,1,0)
    assert capsule((0,3,0),(0,0,0),(0,2,0),2)==(0,4,0)
    assert capsule((0,0,0),(0,0,0),(0,0,0),1)==(1,0,0)
    with pytest.raises(ValueError):sphere((0,0,0),(0,0,0),-1)
    with pytest.raises(ValueError):plane((0,0,0),(0,0,0),0)


def grid(value=0.):return [[value]*5 for _ in range(5)]

@pytest.mark.parametrize('boundary',['fixed','reflecting','dissipative'])
def test_wave_zero_field(boundary):
    h,v=wave(grid(),grid(),h=.1,dx=1,dy=1,c=1,boundary=boundary)
    assert h==v==grid()


def test_wave_one_and_two_impulses_gather_and_stencil():
    initial=grid();v=grid()
    h,v=wave(initial,v,h=.1,dx=1,dy=1,c=1,events=[('a',2,2,1),('a',2,2,1),('b',2,2,2)])
    assert initial==grid() and h[2][2]==pytest.approx(.3) and v[2][2]==3
    next_h,next_v=wave(h,v,h=.1,dx=1,dy=1,c=1)
    assert next_v[2][2]==pytest.approx(2.88) and next_h[2][2]==pytest.approx(.588)
    assert next_h[2][1]==pytest.approx(.003) and next_h[1][2]==pytest.approx(.003)
    assert next_h[0][0]==0


def test_wave_boundaries_and_world_grid_stability():
    for boundary,expected in [('fixed',0),('reflecting',.1),('dissipative',.05)]:
        h,_=wave(grid(),grid(),h=.1,dx=1,dy=1,c=1,boundary=boundary,events=[('a',0,2,1)])
        assert h[0][2]==pytest.approx(expected)
    h,_=wave(grid(2),grid(),h=.1,dx=1,dy=1,c=1,boundary='reflecting')
    assert h==grid(2)
    for dx,c in [(1,10),(.1,1)]:
        with pytest.raises(ValueError,match='CFL'):wave(grid(),grid(),h=.1,dx=dx,dy=dx,c=c)
    # Same world resized: halving spacing requires halving h for same c*h/dx.
    wave(grid(),grid(),h=.05,dx=.1,dy=.1,c=1)

@pytest.mark.parametrize('kwargs',[{'h':0},{'c':float('inf')},{'damping':-1},{'boundary':'unknown'}, {'events':[('a',2,2,1)],'capacity':0},{'events':[('a',9,2,1)]}])
def test_wave_rejects_invalid_inputs(kwargs):
    config=dict(h=.1,dx=1,dy=1,c=1);config.update(kwargs)
    with pytest.raises(ValueError):wave(grid(),grid(),**config)


def test_snapshot_generations_completion_and_all_consumers():
    s=Snapshots();snap=Snapshot(1,4,1,1,4,4,10)
    with pytest.raises(ValueError):s.publish(snap,9)
    with pytest.raises(ValueError):s.publish(Snapshot(1,4,1,1,3,4,10),10)
    s.publish(snap,10)
    for consumer,completion in [('view-a',11),('view-b',12),('shadow',13),('motion-history',14)]:s.consume(1,consumer,completion)
    assert not s.retire(1,{'view-a':99})
    assert not s.retire(1,{'view-a':11,'view-b':12,'shadow':13,'motion-history':13})
    assert s.retire(1,{'view-a':11,'view-b':12,'shadow':13,'motion-history':14})


def test_previous_presented_pose_per_view_not_previous_substep():
    s=Snapshots()
    for i,t in [(1,4),(2,8),(3,12)]:s.publish(Snapshot(i,t,1,1,t,t,i),i)
    assert s.presented('a',1) is None
    assert s.presented('b',2) is None
    assert s.presented('a',3).tick==4
    assert s.presented('b',3).tick==8
    assert s.presented('a',3,teleport=True) is None
    s.publish(Snapshot(4,13,1,2,13,13,4),4)
    assert s.presented('a',4) is None


@pytest.mark.parametrize('kwargs',[dict(max_ticks=1.5),dict(capacity=True),dict(history_capacity=0),dict(step='small')])
def test_clock_rejects_invalid_types(kwargs):
    with pytest.raises(ValueError):Clock(**kwargs)


def test_clock_history_has_explicit_bound_and_overflow():
    c=Clock(history_capacity=1)
    assert c.enqueue('one',0,1)
    c.advance(0,1/60)
    assert not c.enqueue('two',0,1) and c.overflow==1
    for frame,dt in [(True,.1),(1,float('inf')),(1,'long')]:
        with pytest.raises(ValueError):c.advance(frame,dt)
    assert c.tick==1 and c.last_frame==0


@pytest.mark.parametrize('edges,iterations,colors',[([(0.5,1,1,0)],1,None), ([(0,1,1,0)],1.5,None), ([(0,1,1,0)],1,[[True]])])
def test_solver_rejects_noninteger_indices_counts(edges,iterations,colors):
    with pytest.raises(ValueError):solve([(0,0,0),(1,0,0)],[0,1],edges,.1,iterations,colors=colors)


def test_derived_nonfinite_and_underflow_are_rejected():
    with pytest.raises(ValueError):distance((0,0,0),(1,0,0),0,1,1,1,1e-300)
    with pytest.raises(ValueError):integrate((0,0,0),(1e308,0,0),1,(1e308,0,0),(0,0,0),2)
    with pytest.raises(ValueError):wave(grid(),grid(),h=.1,dx=1e-300,dy=1,c=1)
    with pytest.raises(ValueError):wave(grid(),grid(),h=.1,dx=1,dy=1,c=1,events=[('e',1.5,2,1)])


def test_one_way_impact_grid_event_has_identity_tick_and_units():
    from simulation_host_contracts import impact_event
    tick,event=impact_event('drop-7',8,(.5,.25,0),-2,width=5,height=5,extent=1,scale_factor=.1)
    assert tick==8 and event==('drop-7',1,2,.2)
    h,v=wave(grid(),grid(),h=.1,dx=1,dy=1,c=1,events=[event,event])
    assert v[1][2]==pytest.approx(.2) and h[1][2]==pytest.approx(.02)
    assert impact_event('up',8,(0,0,0),2,width=5,height=5,extent=1)[1][-1]==0
    with pytest.raises(ValueError):impact_event('out',8,(-.1,0,0),-1,width=5,height=5,extent=1)
