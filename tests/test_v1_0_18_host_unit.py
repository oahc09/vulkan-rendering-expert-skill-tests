"""CPU simulations only; no GPU, JNI, DirectWrite or visual acceptance."""
import pytest
from text_host_contracts import GlyphKey, AtlasSlot, provider_glyph, linear_over, checked_budget
pytestmark=pytest.mark.host_unit

def key(**kw):
    data=dict(provider='system',face='fontA',face_generation=1,glyph=42,variation=(),representation='coverage',pixel_size=16)
    data.update(kw);return GlyphKey(**data)

@pytest.mark.parametrize('field,value', [('face','fontB'),('provider','other'),('face_generation',2),('glyph',43),('variation',(('wght',600.),)),('representation','msdf'),('pixel_size',24)])
def test_cache_identity(field,value):
    assert key()!=key(**{field:value})

@pytest.mark.parametrize('glyph,bits', [(65536,16),(-1,32),(2**32,32),(True,16),(1.5,16)])
def test_wide_id_never_truncated(glyph,bits):
    with pytest.raises(ValueError):provider_glyph(glyph,bits)

def test_supported_range_not_platform_claim():
    assert provider_glyph(65535,16)==65535
    assert provider_glyph(65536,24)==65536

@pytest.mark.parametrize('value', [float('nan'),float('inf')])
def test_invalid_axis_rejected(value):
    with pytest.raises(ValueError):key(variation=(('wght',value),))

def test_upload_face_cancellation_and_stale_publication():
    s=AtlasSlot('A');g=s.prepare(key(),'A',2,{})
    assert not s.publish(g,1,1)
    assert not s.publish(g,2,2) # late old face task
    assert not s.reusable({'upload':1})
    assert s.reusable({'upload':2}) # cancelled upload retired, not shown
    n=s.prepare(key(face_generation=2),'A',3,{'upload':2})
    assert not s.publish(g,1,3)
    assert s.publish(n,2,3)

def test_snapshot_and_all_queues_must_retire():
    s=AtlasSlot('A');g=s.prepare(key(),'A',1,{})
    assert s.publish(g,1,1)
    s.retain(g);s.submit(g,'A','graphics',4);s.submit(g,'A','preview',7)
    assert not s.reusable({'upload':1,'graphics':4,'preview':7})
    s.release()
    assert not s.reusable({'upload':1,'graphics':4,'preview':6})
    with pytest.raises(ValueError):s.prepare(key(glyph=88),'A',2,{'upload':1,'graphics':4})
    assert s.reusable({'upload':1,'graphics':4,'preview':7})
    s.prepare(key(glyph=88),'A',2,{'upload':1,'graphics':4,'preview':7})
    with pytest.raises(ValueError):s.retain(g)

def test_device_isolation_and_underflow():
    s=AtlasSlot('A')
    with pytest.raises(ValueError):s.prepare(key(),'B',1,{})
    g=s.prepare(key(),'A',1,{});s.publish(g,1,1);s.retain(g)
    with pytest.raises(ValueError):s.submit(g,'B','q',1)
    s.release()
    with pytest.raises(ValueError):s.release()

def test_alpha_reference():
    assert linear_over(.5,.8,1.,.2)==pytest.approx(.52,abs=1e-12)
    assert linear_over(0.,1.,1.,.2)==.2
    assert linear_over(1.,1.,1.,.2)==1.

@pytest.mark.parametrize('value',[-1,2,float('nan'),float('inf')])
def test_invalid_coverage(value):
    with pytest.raises(ValueError):linear_over(value,.8,1.,.2)

@pytest.mark.parametrize('field', ['segments','depth','vertices','bytes_used'])
def test_each_work_limit_fails_closed(field):
    values=dict(segments=4096,depth=16,vertices=65536,bytes_used=2**20)
    assert checked_budget(**values)
    values[field]+=1;assert not checked_budget(**values)
    values[field]=-1
    with pytest.raises(ValueError):checked_budget(**values)


@pytest.mark.parametrize('change',[
    {'synthetic_style':'bold'}, {'palette':1}, {'subpixel_phase':(.25,0)},
    {'distance_range':4}, {'render_mode':'hinted'}, {'generation_options':('edge-coloring-v2',)},
])
def test_raster_options_do_not_alias(change):
    from dataclasses import replace
    base=GlyphKey('provider','face',1,42,(),'coverage',16)
    assert base != replace(base,**change)


@pytest.mark.parametrize('bad_upload',[-1,True,2**32,'1'])
def test_prepare_failure_is_atomic(bad_upload):
    from copy import deepcopy
    slot=AtlasSlot('device');before=deepcopy(slot.__dict__)
    key=GlyphKey('provider','face',1,42,(),'coverage',16)
    with pytest.raises(ValueError):slot.prepare(key,'device',bad_upload,{})
    assert slot.__dict__==before

def test_prepare_generation_overflow_is_atomic():
    from copy import deepcopy
    slot=AtlasSlot('device',2**32-1);before=deepcopy(slot.__dict__)
    key=GlyphKey('provider','face',1,42,(),'coverage',16)
    with pytest.raises(ValueError):slot.prepare(key,'device',1,{})
    assert slot.__dict__==before

@pytest.mark.parametrize('options',[(float('nan'),),((float('inf'),),),([],),({'a':1},)])
def test_generation_options_reject_noncanonical(options):
    with pytest.raises(ValueError):GlyphKey('provider','face',1,42,(),'coverage',16,generation_options=options)
