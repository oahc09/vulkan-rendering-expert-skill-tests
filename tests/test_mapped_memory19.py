from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import mapped_memory19 as m
pytestmark=pytest.mark.host_unit
BASE=dict(allocation_size=1024,map_offset=0,map_size=m.WHOLE,offset=0,size=64,atom=64)
def check(**k):return m.check_range(**(BASE|k))
def test_aligned():assert check()['status']=='VALID_RANGE_ONLY'
@pytest.mark.parametrize('change,vuid',[
 ({'mapped':False},'00684'),({'offset':1},'00687'),({'map_offset':64},'00685'),({'size':1088},'00685'),({'size':65},'01390'),({'size':m.WHOLE,'offset':1024},'00686'),({'map_size':65,'size':m.WHOLE},'01389')])
def test_named_rules(change,vuid):assert any(x.endswith(vuid) for x in check(**change)['vuids'])
def test_allocation_end_exception():assert check(allocation_size=1000,offset=960,size=40)['vuids']==[]
def test_whole_ends_mapping_not_allocation():assert check(map_size=128,size=m.WHOLE)['effective_end']==128
def test_whole_at_partial_unaligned_mapping_end():assert any(x.endswith('01389') for x in check(map_size=129,size=m.WHOLE)['vuids'])
@pytest.mark.parametrize('field,value',[('atom',0),('atom',3),('offset',True),('size',-1),('allocation_size',1<<64),('map_size',2048)])
def test_bad_input(field,value):
 with pytest.raises(ValueError):check(**{field:value})
def test_expansion_requires_neighbor_ownership():
 r=m.expand_access(allocation_size=1024,map_offset=0,map_size=1024,offset=65,length=2,atom=64)
 assert (r['offset'],r['size'],r['status'])==(64,64,'RANGE_READY_REQUIRES_ATOM_OWNERSHIP')
def test_mapping_does_not_cover_expanded_access():
 assert m.expand_access(allocation_size=1024,map_offset=65,map_size=10,offset=66,length=1,atom=64)['status']=='REMAP_REQUIRED'
FACTS=dict(direction='readback',coherent=False,completed=True,host_dirty=False,access_exclusive=True,atom_exclusive=True,host_ordered=True,device_host_barrier=True)
def test_noncoherent_readback():assert m.visibility_obligations(**FACTS)['actions']==['invalidate_after_wait_before_read']
@pytest.mark.parametrize('change,status',[({'completed':False},'WAIT_RELEVANT_DEVICE_USES'),({'host_dirty':True},'REJECTED_UNFLUSHED_HOST_WRITES'),({'atom_exclusive':False},'REJECTED_ATOM_RACE'),({'host_ordered':False},'REQUIRE_HOST_HAPPENS_BEFORE'),({'device_host_barrier':False},'REQUIRE_DEVICE_TO_HOST_DEPENDENCY')])
def test_visibility_negatives(change,status):assert m.visibility_obligations(**(FACTS|change))['status']==status
def test_coherent_not_completion_or_barrier():
 assert m.visibility_obligations(**(FACTS|{'coherent':True}))['actions']==[]
 assert m.visibility_obligations(**(FACTS|{'coherent':True,'completed':False}))['status']=='WAIT_RELEVANT_DEVICE_USES'
def test_upload_flush_before_submit():assert m.visibility_obligations(**(FACTS|{'direction':'upload'}))['actions']==['flush_before_submission']

@pytest.mark.parametrize('field',['size','map_size'])
def test_numeric_whole_requires_explicit_serialization(field):
 with pytest.raises(ValueError):check(**{field:m.MAX})
def test_coherent_has_no_noncoherent_atom_or_dirty_cache_obligation():
 assert m.visibility_obligations(**(FACTS|{'coherent':True,'atom_exclusive':False,'host_dirty':True}))['status']=='READY_WITHIN_FACTS'
 assert m.visibility_obligations(**(FACTS|{'coherent':True,'access_exclusive':False}))['status']=='REJECTED_ACCESS_RACE'

def test_actual_capability_and_source_pair_do_not_claim_noncoherent_pass():
 import hashlib,json
 root=Path(__file__).parents[1]
 r=json.loads((root/'coverage/v1.0.19/mapped-memory.json').read_text())
 assert hashlib.sha256((root/'cases19/mapped_memory/probe.c').read_bytes()).hexdigest()==r['source_sha256']
 assert hashlib.sha256((root/'cases19/mapped_memory/run.py').read_bytes()).hexdigest()==r['runner_sha256']
 eligible=[t for d in r['devices'] for t in d['memoryTypes'] if d['memoryTypeBits']&(1<<t['index']) and t['flags']&2 and not t['flags']&4]
 assert not eligible
 assert r['cases']['visibility']['result']['status']=='UNAVAILABLE_NOT_RUN'
 assert r['cases']['good']['diagnostics']==[]
 for mode in ('offset','size'):
  assert r['cases'][mode]['diagnostics']==['VUID VUID-VkMappedMemoryRange-size-00685']
  assert r['cases'][mode]['result']['flushResult']==-1000011001
