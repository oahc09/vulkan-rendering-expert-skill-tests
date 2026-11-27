"""SC source/preflight CPU contracts; not SC target execution."""
import importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import sc19_audit as a
import sc19_contract as c
pytestmark=pytest.mark.host_unit
D=json.loads((ROOT/'coverage/v1.0.19/sc-core-delta.json').read_text())
def test_removed_command_negative():
 r=a.assess(D,['vkFreeMemory','vkDestroyCommandPool','vkCreateInstance'])
 assert r['status']=='REQUIRES_SC_REDESIGN' and len(r['core_removed_references'])==2
@pytest.mark.parametrize('symbols',[[],['vkCreateInstance'],['vkTotallyUnknown']])
def test_no_removed_never_means_supported(symbols):assert a.assess(D,symbols)['status']=='UNVERIFIED'
def test_wrong_source_rejected():
 with pytest.raises(ValueError):a.extract(b'<registry/>')
def test_removed_features_stay_qualified():
 rows=[r for r in D['records'] if r['operation']=='remove' and r['kind']=='feature']
 assert len(rows)==4 and all(r['struct'] for r in rows)
def pool(recycle,current=1,total=4,size=128):return c.pipeline_pool(requested_size=size,reservations=[dict(poolEntrySize=128,poolEntryCount=2),dict(poolEntrySize=128,poolEntryCount=1)],current_count=current,total_ever_created=total,recycle=recycle)
def test_nonrecycling_uses_cumulative():
 assert pool(True)['status']=='WITHIN_POOL_COUNT_ONLY'
 assert pool(False)['status']=='REJECTED'
def test_boundary_counts():
 assert pool(True,current=2)['status']=='WITHIN_POOL_COUNT_ONLY'
 assert pool(True,current=3)['status']=='REJECTED'
def test_size_and_unknown():
 assert pool(True,size=256)['rule']=='05028'
 assert pool(None)['status']=='UNKNOWN'
@pytest.mark.parametrize('value',[True,-1,1.5,2**64])
def test_bad_count(value):
 with pytest.raises(ValueError):pool(True,current=value)
def test_fault_incomplete_preserved():
 for result,unrecorded in [('VK_INCOMPLETE',False),('VK_SUCCESS',True)]:
  assert c.fault_completeness(result=result,unrecorded=unrecorded,count=1,capacity=2,max_query_count=2,data_requested=True)=='INCOMPLETE_EVIDENCE'
def test_fault_capacity_rejected():
 with pytest.raises(ValueError):c.fault_completeness(result='VK_SUCCESS',unrecorded=False,count=3,capacity=2,max_query_count=2,data_requested=True)

def test_nm_versions():
 assert a.nm_symbols(b' U vkFreeMemory@VULKAN_1.0\n U vkCreateInstance\n U malloc\n')==['vkCreateInstance','vkFreeMemory']
def test_wrong_audit_provenance():
 with pytest.raises(ValueError):a.assess({'source_sha256':'wrong'},[])

def test_u32_api_fields():
 with pytest.raises(ValueError):c.pipeline_pool(requested_size=128,reservations=[dict(poolEntrySize=128,poolEntryCount=2**32)],current_count=0,total_ever_created=0,recycle=True)
 with pytest.raises(ValueError):c.fault_completeness(result='VK_SUCCESS',unrecorded=False,count=0,capacity=2**32,max_query_count=2**32,data_requested=True)
def test_fault_count_only_not_data():
 assert c.fault_completeness(result='VK_SUCCESS',unrecorded=False,count=1,capacity=2,max_query_count=2,data_requested=False)=='COUNT_QUERY_ONLY'
