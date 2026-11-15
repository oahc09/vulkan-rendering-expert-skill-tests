"""CPU routing/capacity/failure invariants, separate from actual Vulkan fixture."""
import pytest
from text_atlas_pages import AtlasPages
from text_host_contracts import GlyphKey
pytestmark=pytest.mark.host_unit

def key(face=1):return GlyphKey('trusted','face',face,42,(),'coverage',16)
def pool(**kw):
    handles=[];dead=[]
    def alloc(extent):h=object();handles.append(h);return h
    return AtlasPages('A',alloc,dead.append,**kw),handles,dead

def test_grow_retains_old_snapshots_then_reclaims():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{})
    assert p.publish(*a,1,1);old=p.capture()
    b=p.prepare(key(),(32,32),2,{'upload':1})
    assert not p.publish(*b,1,1) and p.current==a
    assert p.publish(*b,1,2);new=p.capture()
    p.submit(old,'A','draw',3);p.release(old)
    assert not p.collect({'upload':2,'draw':2})
    assert p.collect({'upload':2,'draw':3})==[a[0]]
    assert d==[h[0]] and p.payload_bytes==1024 and p.current==b
    p.submit(new,'A','draw',4);p.release(new)
    assert not p.collect({'upload':2,'draw':4})  # current route remains owned

@pytest.mark.parametrize('phase',['before_upload','after_upload'])
def test_cancel_growth_never_replaces_old_route(phase):
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.publish(*a,1,1)
    b=p.prepare(key(),(32,32),2,{'upload':1})
    assert p.cancel(*b) and not p.publish(*b,1,2)
    assert p.current==a
    if phase=='before_upload':assert p.collect({'upload':1})==[]
    assert p.collect({'upload':2})==[b[0]] and d==[h[1]]

@pytest.mark.parametrize('extent',[(0,2),(4097,2),(True,2),(32,),[32,32]])
def test_invalid_growth_never_calls_allocator(extent):
    p,h,d=pool()
    with pytest.raises(ValueError):p.prepare(key(),extent,1,{})
    assert not h and not p.pages and p.next_identity==1

def test_budget_overflow_is_atomic():
    p,h,d=pool(max_payload_bytes=256);p.prepare(key(),(16,16),1,{})
    with pytest.raises(ValueError):p.prepare(key(),(1,1),2,{})
    assert len(h)==1 and p.payload_bytes==256

def test_allocator_failure_keeps_old_page_and_next_id():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.publish(*a,1,1)
    def fail(_):raise MemoryError('injected atomic allocation failure')
    p.allocate=fail
    with pytest.raises(MemoryError):p.prepare(key(),(32,32),2,{'upload':1})
    assert p.current==a and list(p.pages)==[1] and p.next_identity==2 and not d

def test_stale_face_growth_not_published():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{})
    assert not p.publish(*a,2,1) and p.current is None
    p.cancel(*a);assert p.collect({'upload':1})==[a[0]]

def test_cancel_published_retains_captured_consumers():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.publish(*a,1,1);s=p.capture()
    p.cancel(*a)
    with pytest.raises(ValueError):p.capture()
    p.submit(s,'A','draw',9);p.release(s)
    assert not p.collect({'upload':1,'draw':8})
    assert p.collect({'upload':1,'draw':9})==[a[0]]
    with pytest.raises(ValueError):p.submit(s,'A','draw',10)

def test_failed_disposal_keeps_ownership_for_retry():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.cancel(*a)
    def fail(_):raise RuntimeError('dispose failed before destroying')
    p.dispose=fail
    with pytest.raises(RuntimeError):p.collect({'upload':1})
    assert a[0] in p.pages
    p.dispose=d.append;assert p.collect({'upload':1})==[a[0]]

def test_retired_identity_cannot_alias_new_page():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.cancel(*a);p.collect({'upload':1})
    b=p.prepare(key(),(16,16),2,{'upload':1});assert b[0]!=a[0]
    assert not p.cancel(*a) and not p.publish(*a,1,2)

def test_reserved_upload_cannot_alias_two_pending_pages():
    p,h,d=pool();p.prepare(key(),(16,16),5,{})
    with pytest.raises(ValueError):p.prepare(key(),(16,16),5,{})
    assert len(h)==1

def test_publication_cannot_roll_route_backwards():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.publish(*a,1,1)
    b=p.prepare(key(),(32,32),2,{'upload':1});p.publish(*b,1,2)
    assert not p.publish(*a,1,2) and p.current==b

def test_cross_page_consumer_domain_monotonic():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.publish(*a,1,1);old=p.capture()
    b=p.prepare(key(),(32,32),2,{'upload':1});p.publish(*b,1,2);new=p.capture()
    p.submit(new,'A','draw',10)
    with pytest.raises(ValueError):p.submit(old,'A','draw',9)
    p.submit(old,'A','draw',10) # same actual submission can reference two pages

def test_max_pages_counts_cancelled_pending_upload():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{});p.cancel(*a)
    p.prepare(key(),(16,16),2,{})
    with pytest.raises(ValueError):p.prepare(key(),(16,16),3,{})
    assert len(h)==2 and not p.collect({'upload':0})

def test_invalid_completion_rejected_before_collection():
    p,h,d=pool()
    with pytest.raises(ValueError):p.collect({'upload':True})

def test_null_allocator_does_not_reserve_upload():
    p,h,d=pool();p.allocate=lambda _:None
    with pytest.raises(ValueError):p.prepare(key(),(16,16),1,{})
    assert p.reserved_upload==0 and not p.pages


def test_completed_unpublished_candidate_keeps_ownership():
    p,h,d=pool();a=p.prepare(key(),(16,16),1,{})
    assert p.collect({'upload':1})==[] and not d
    assert p.publish(*a,1,1) and p.current==a
