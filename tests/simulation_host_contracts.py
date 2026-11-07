"""FP64 host oracles, not a physics engine or GPU correctness evidence.

Jacobi sums contributions (no degree normalization), relaxation 1 by default.
Wave is symplectic velocity/height with central spatial differences. Its linear
undamped CFL bound is checked with a configurable margin; other models need
independent analysis. All negative tests reject on host, never fault a device.
"""
from dataclasses import dataclass, field
from math import isfinite, sqrt, floor, hypot


def finite(*xs):
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x) for x in xs):
        raise ValueError('non-finite input')


def positive(*xs):
    finite(*xs)
    if any(x <= 0 for x in xs):
        raise ValueError('positive values required')


def vec(v):
    if len(v) != 3:
        raise ValueError('3D vector required')
    finite(*v)
    return tuple(v)


def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def scale(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return hypot(*a)

def integer(value,minimum=0):
    if type(value) is not int or value<minimum: raise ValueError('integer capacity/index required')


@dataclass
class Clock:
    step: float = 1/60
    max_ticks: int = 4
    tick: int = 0
    accumulator: float = 0.
    dropped_time: float = 0.
    paused: bool = False
    last_frame: int = -1
    consumed: set = field(default_factory=set)
    pending: dict = field(default_factory=dict)
    capacity: int = 64
    overflow: int = 0
    history_capacity: int = 4096

    def __post_init__(self):
        positive(self.step)
        integer(self.max_ticks,1);integer(self.capacity,1);integer(self.history_capacity,1)
        if self.max_ticks < 1 or self.capacity < 1:
            raise ValueError('invalid capacity')

    def enqueue(self, event_id, timestamp, impulse):
        if not isinstance(event_id,str) or not event_id: raise ValueError('event identity')
        finite(timestamp,impulse)
        if timestamp < 0: raise ValueError('negative timestamp')
        if event_id in self.consumed or event_id in self.pending: return False
        if len(self.pending) >= self.capacity or len(self.pending)+len(self.consumed)>=self.history_capacity:
            self.overflow += 1
            return False
        self.pending[event_id]=(timestamp,impulse)
        return True

    def advance(self, frame_id, dt):
        """One owner call per monotone frame id; duplicate view calls do no work.

        Paused wall time is counted as dropped; timestamp inputs use simulation
        time. Resume is freeze-world-time, not catch-up. Events in dropped wall
        time require the caller's explicit mapping to simulation timestamps.
        """
        finite(dt);integer(frame_id)
        finite(self.accumulator+dt,self.dropped_time+dt,(self.accumulator+dt)/self.step)
        if dt < 0 or frame_id < self.last_frame: raise ValueError('invalid clock input')
        if frame_id == self.last_frame: return []
        self.last_frame=frame_id
        if self.paused:
            self.dropped_time += dt
            return []
        self.accumulator += dt
        due=floor((self.accumulator+self.step*1e-10)/self.step)
        count=min(due,self.max_ticks)
        self.dropped_time += max(0,due-count)*self.step
        self.accumulator=max(0.,self.accumulator-due*self.step)
        out=[]
        for _ in range(count):
            self.tick+=1
            events=[]
            for eid,(when,value) in list(self.pending.items()):
                if when <= self.tick*self.step+self.step*1e-10:
                    events.append((eid,value)); self.consumed.add(eid); del self.pending[eid]
            out.append((self.tick,events))
        return out


def integrate(x,velocity,inverse_mass,force,impulse,h):
    positive(h); finite(inverse_mass)
    if inverse_mass<0: raise ValueError('negative mass')
    for v in (x,velocity,force,impulse): vec(v)
    if inverse_mass==0: return tuple(x),tuple(velocity)
    v=add(velocity,scale(add(scale(force,h),impulse),inverse_mass))
    result=add(x,scale(v,h));vec(result);vec(v)
    return result,v


def distance(a,b,wa,wb,rest,alpha,h,lam=0.):
    """Return corrected endpoints and accumulated multiplier for ONE iteration."""
    a,b=vec(a),vec(b); positive(h); finite(wa,wb,rest,alpha,lam)
    if min(wa,wb,rest,alpha)<0: raise ValueError('negative solver parameter')
    d=vec(sub(b,a)); length=norm(d);finite(length)
    if length==0 or wa+wb==0: return a,b,lam
    square=h*h
    if square==0 or not isfinite(square):raise ValueError('unsupported squared step')
    at=alpha/square;finite(at,wa+wb+at)
    dl=(-(length-rest)-at*lam)/(wa+wb+at)
    n=scale(d,1/length)
    result=(vec(add(a,scale(n,-wa*dl))),vec(add(b,scale(n,wb*dl))),lam+dl);finite(result[2])
    return result


def lambda_policy(previous,current):
    """Baseline reset per substep; same substep retains only identical contract."""
    return 'retain' if previous==current else 'reset'


def validate_edges(positions,masses,edges):
    if not positions or len(positions)!=len(masses): raise ValueError('mass length')
    for p in positions: vec(p)
    finite(*masses)
    if any(w<0 for w in masses): raise ValueError('negative mass')
    for a,b,rest,alpha in edges:
        integer(a);integer(b)
        if not (0<=a<len(positions) and 0<=b<len(positions)) or a==b: raise ValueError('edge index')
        finite(rest,alpha)
        if min(rest,alpha)<0: raise ValueError('edge parameter')


def solve(positions,masses,edges,h,iterations,*,colors=None,relaxation=1.):
    """One substep: colored GS or Jacobi sum/gather; no universal convergence claim."""
    validate_edges(positions,masses,edges); positive(h)
    finite(relaxation);integer(iterations,1)
    if not 0<relaxation<=1 or iterations<1: raise ValueError('solver configuration')
    x=list(map(tuple,positions)); lambdas=[0.]*len(edges)
    if colors is not None:
        for group in colors:
            for i in group:integer(i)
        if sorted(i for group in colors for i in group)!=list(range(len(edges))): raise ValueError('color coverage')
        for group in colors:
            written=set()
            for i in group:
                writable={p for p in edges[i][:2] if masses[p]>0}
                if written & writable: raise ValueError('color write conflict')
                written |= writable
    for _ in range(iterations):
        if colors is None:
            contributions=[(0.,0.,0.) for _ in x]
            for i,(a,b,r,alpha) in enumerate(edges):
                aa,bb,ll=distance(x[a],x[b],masses[a],masses[b],r,alpha,h,lambdas[i])
                contributions[a]=add(contributions[a],sub(aa,x[a]))
                contributions[b]=add(contributions[b],sub(bb,x[b]))
                lambdas[i]+=relaxation*(ll-lambdas[i])
            x=[add(p,scale(delta,relaxation)) for p,delta in zip(x,contributions)]
        else:
            for group in colors:
                for i in group:
                    a,b,r,alpha=edges[i]
                    x[a],x[b],lambdas[i]=distance(x[a],x[b],masses[a],masses[b],r,alpha,h,lambdas[i])
    return x,lambdas


def plane(point,normal,offset):
    point,normal=vec(point),vec(normal);finite(offset);positive(norm(normal))
    n=scale(normal,1/norm(normal));depth=dot(point,n)-offset
    return sub(point,scale(n,min(depth,0.)))


def sphere(point,center,radius):
    point,center=vec(point),vec(center);finite(radius)
    if radius<0: raise ValueError('radius')
    d=sub(point,center);length=norm(d)
    if length>=radius: return point
    return add(center,scale(d,radius/length)) if length else add(center,(radius,0.,0.))


def capsule(point,a,b,radius):
    point,a,b=vec(point),vec(a),vec(b);ab=sub(b,a);den=dot(ab,ab)
    t=max(0.,min(1.,dot(sub(point,a),ab)/den)) if den else 0.
    return sphere(point,add(a,scale(ab,t)),radius)


def wave(height,velocity,*,h,dx,dy,c,damping=0.,boundary='fixed',events=(),capacity=64,margin=.95):
    """Each cell gathers bounded (eventId,row,col,impulse) events exactly once.

    Event lifetime is owned by Clock. Duplicate IDs in this batch are ignored;
    capacity overflow rejects the whole batch rather than silently truncating.
    Fixed edges zero h/v; reflecting edges clamp neighbors (zero normal flux);
    dissipative edges additionally multiply velocity by 0.5 each step.
    """
    positive(h,dx,dy);finite(c,damping,margin)
    if c<0 or damping<0 or not 0<margin<=1: raise ValueError('wave parameter')
    if dx*dx==0 or dy*dy==0:raise ValueError('unsupported spacing')
    if c*h*hypot(1/dx,1/dy)>margin: raise ValueError('CFL limit')
    if boundary not in ('fixed','reflecting','dissipative'): raise ValueError('boundary')
    ny=len(height);nx=len(height[0]) if ny else 0
    if min(nx,ny)<3 or len(velocity)!=ny: raise ValueError('grid')
    for row in list(height)+list(velocity):
        if len(row)!=nx: raise ValueError('ragged grid')
        finite(*row)
    integer(capacity)
    if capacity<0 or len(events)>capacity: raise ValueError('event overflow')
    sources={};seen=set()
    for eid,y,x,impulse in events:
        integer(y);integer(x)
        if not isinstance(eid,str) or not eid:raise ValueError('event identity')
        finite(impulse)
        if not (0<=y<ny and 0<=x<nx): raise ValueError('event bounds')
        if eid not in seen:
            sources[y,x]=sources.get((y,x),0.)+impulse; seen.add(eid)
    hh=[[0.]*nx for _ in range(ny)];vv=[[0.]*nx for _ in range(ny)]
    for y in range(ny):
        for x in range(nx):
            edge=y in (0,ny-1) or x in (0,nx-1)
            if boundary=='fixed' and edge: continue
            lap=(height[y][max(0,x-1)]-2*height[y][x]+height[y][min(nx-1,x+1)])/dx**2
            lap+=(height[max(0,y-1)][x]-2*height[y][x]+height[min(ny-1,y+1)][x])/dy**2
            vv[y][x]=(velocity[y][x]+sources.get((y,x),0.)+h*c*c*lap)/(1+h*damping)
            if edge and boundary=='dissipative': vv[y][x]*=.5
            hh[y][x]=height[y][x]+h*vv[y][x];finite(hh[y][x],vv[y][x])
    return hh,vv


@dataclass(frozen=True)
class Snapshot:
    id: int
    tick: int
    world: int
    topology: int
    normal_tick: int
    bounds_tick: int
    completion: int


class Snapshots:
    def __init__(self):
        self.snapshots={};self.readers={};self.history={}

    def publish(self,snapshot,completed):
        for value in (snapshot.id,snapshot.tick,snapshot.world,snapshot.topology,snapshot.normal_tick,snapshot.bounds_tick,snapshot.completion,completed):integer(value)
        if snapshot.id in self.snapshots or min(snapshot.id,snapshot.tick,snapshot.world,snapshot.topology,snapshot.completion)<0:
            raise ValueError('snapshot identity')
        if snapshot.tick!=snapshot.normal_tick or snapshot.tick!=snapshot.bounds_tick or snapshot.completion>completed:
            raise ValueError('incomplete/mixed snapshot')
        self.snapshots[snapshot.id]=snapshot;self.readers[snapshot.id]={}

    def consume(self,sid,consumer,completion):
        integer(sid);integer(completion)
        if not isinstance(consumer,str) or not consumer:raise ValueError("consumer identity")
        if sid not in self.snapshots or completion<self.snapshots[sid].completion: raise ValueError('consumer')
        self.readers[sid][consumer]=max(completion,self.readers[sid].get(consumer,0))

    def presented(self,view,sid,*,teleport=False):
        current=self.snapshots[sid];previous=self.history.get(view)
        valid=previous is not None and not teleport and (previous.world,previous.topology)==(current.world,current.topology)
        self.history[view]=current
        return previous if valid else None

    def retire(self,sid,completed):
        # completed maps each actual consumer to its own timeline, never a max
        # across independent queues. Destroying a surface does not imply signal.
        if any(completed.get(c,-1)<v for c,v in self.readers[sid].items()): return False
        # Host history metadata persists; storage references must be held as
        # explicit consumers until the motion pass completes.
        del self.readers[sid];del self.snapshots[sid]
        return True


def impact_event(event_id,tick,position,normal_velocity,*,width,height,extent,scale_factor=1.):
    """One-way particle impact -> heightfield event. Caller deduplicates by tick/ID.

    Coordinates are world XY over [0,extent]; the boundary is explicit reject,
    not wrap or clamp. This produces no feedback force on the particle pool.
    """
    integer(tick);integer(width,3);integer(height,3);positive(extent)
    if not isinstance(event_id,str) or not event_id:raise ValueError('event identity')
    x,y,_=vec(position);finite(normal_velocity,scale_factor)
    if not 0<=x<=extent or not 0<=y<=extent or scale_factor<0:raise ValueError('impact domain')
    impulse=max(0.,-normal_velocity)*scale_factor;finite(impulse)
    return tick,(event_id,round(y/extent*(height-1)),round(x/extent*(width-1)),impulse)
