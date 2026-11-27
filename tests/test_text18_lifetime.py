"""CPU lifecycle regressions, not GPU, concurrency or platform acceptance."""
from copy import deepcopy
import pytest
from text_host_contracts import AtlasSlot, GlyphKey
pytestmark = pytest.mark.host_unit

def key():
    return GlyphKey('system','face',1,42,(),'coverage',16)

def ready():
    s=AtlasSlot('A');g=s.prepare(key(),'A',1,{})
    assert s.publish(g,1,1)
    return s,g

@pytest.mark.parametrize('value',[0,1])
def test_new_upload_cannot_reuse_completed_signal(value):
    s,g=ready();before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.prepare(key(),'A',value,{'upload':1})
    assert s.__dict__==before

def test_first_upload_cannot_use_already_observed_signal():
    s=AtlasSlot('A')
    with pytest.raises(ValueError):s.prepare(key(),'A',4,{'upload':4})

@pytest.mark.parametrize('completed',[{'upload':-1},{'q':True},{'':1},[],{'q':'1'}])
def test_empty_slot_still_validates_observed_completions(completed):
    s=AtlasSlot('A');before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.prepare(key(),'A',1,completed)
    assert s.__dict__==before

@pytest.mark.parametrize('queue',['upload','',None])
def test_consumer_timeline_cannot_alias_upload(queue):
    s,g=ready();s.retain(g);before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.submit(g,'A',queue,2)
    assert s.__dict__==before

def test_cancel_is_terminal_for_publication_but_not_early_retirement():
    s=AtlasSlot('A');g=s.prepare(key(),'A',2,{})
    assert s.cancel(g)
    assert not s.publish(g,1,2)
    with pytest.raises(ValueError):s.retain(g)
    assert not s.reusable({'upload':1})
    assert s.reusable({'upload':2})
    newer=s.prepare(key(),'A',3,{'upload':2})
    assert not s.cancel(g)
    assert s.publish(newer,1,3)

def test_cancel_preserves_captured_snapshot_obligations():
    s,g=ready();s.retain(g);s.cancel(g)
    with pytest.raises(ValueError):s.retain(g)
    s.submit(g,'A','graphics',4);s.submit(g,'A','preview',7)
    s.release()
    assert not s.reusable({'upload':1,'graphics':4,'preview':6})
    assert s.reusable({'upload':1,'graphics':4,'preview':7})

def test_duplicate_same_submission_allowed_but_signal_regression_rejected():
    s,g=ready();s.retain(g)
    s.submit(g,'A','graphics',4);s.submit(g,'A','graphics',4)
    with pytest.raises(ValueError):s.submit(g,'A','graphics',3)
    s.release()
    n=s.prepare(key(),'A',2,{'upload':1,'graphics':4});s.publish(n,1,2);s.retain(n)
    with pytest.raises(ValueError):s.submit(n,'A','graphics',4)
    s.submit(n,'A','graphics',5);s.release()
    assert not s.reusable({'upload':2,'graphics':4})
    assert s.reusable({'upload':2,'graphics':5})

def test_two_snapshots_and_two_devices_not_confused():
    s,g=ready();s.retain(g);s.retain(g)
    s.submit(g,'A','q1',3);s.submit(g,'A','q2',8);s.release()
    assert not s.reusable({'upload':1,'q1':3,'q2':8})
    s.release()
    with pytest.raises(ValueError):s.prepare(key(),'B',2,{'upload':1,'q1':3,'q2':8})
    assert not s.reusable({'upload':1,'q1':3})


def test_timeline_values_use_uint64_without_truncation():
    high=2**32+17
    s=AtlasSlot('A');g=s.prepare(key(),'A',high,{'upload':high-1})
    assert not s.publish(g,1,high-1)
    assert s.publish(g,1,high)
    s.retain(g);s.submit(g,'A','graphics',2**64-1);s.release()
    assert not s.reusable({'upload':high,'graphics':2**64-2})
    assert s.reusable({'upload':high,'graphics':2**64-1})


@pytest.mark.parametrize('bad',[True,False,-1,2**64])
def test_all_timeline_inputs_reject_invalid_uint64_atomically(bad):
    s=AtlasSlot('A');before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.prepare(key(),'A',bad,{})
    assert s.__dict__==before
    with pytest.raises(ValueError):s.prepare(key(),'A',1,{'upload':bad})
    assert s.__dict__==before
    s,g=ready();before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.publish(g,1,bad)
    assert s.__dict__==before
    s.retain(g);before=deepcopy(s.__dict__)
    with pytest.raises(ValueError):s.submit(g,'A','graphics',bad)
    assert s.__dict__==before
    with pytest.raises(ValueError):s.reusable({'upload':bad})
    assert s.__dict__==before
