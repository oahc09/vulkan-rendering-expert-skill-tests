import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.dynamic_ubo19 import bind,reuse

def config():return dict(alignment=16,bufferSize=64,descriptorCount=2,range=16,baseOffset=0,maxUniformRange=65536,maxDynamicUBO=8,maxStageUBO=12)
def test_legal_swap_not_vuid():
 assert bind(config(),[0,16])['vuids']==[];assert bind(config(),[16,0])['vuids']==[]
@pytest.mark.parametrize('off,suffix',[([0],'dynamicOffsetCount-00359'),([1,16],'pDynamicOffsets-01971'),([0,64],'pDescriptorSets-01979')])
def test_invalid(off,suffix):assert bind(config(),off)['vuids']==['VUID-vkCmdBindDescriptorSets-'+suffix]
def test_unknown():assert bind({},[0,16])['status']=='UNKNOWN'
@pytest.mark.parametrize('k,v,status',[('descriptorCount',1,'OUT_OF_SCOPE'),('range',32,'OUT_OF_SCOPE'),('maxDynamicUBO',1,'UNSUPPORTED_LIMITS'),('maxStageUBO',1,'UNSUPPORTED_LIMITS'),('maxUniformRange',8,'UNSUPPORTED_LIMITS')])
def test_limits(k,v,status):
 m=config();m[k]=v;assert bind(m,[0,16])['status']==status
@pytest.mark.parametrize('off',[[False,16],[1<<32,0],[-1,0]])
def test_types(off):
 with pytest.raises(ValueError):bind(config(),off)
def test_unused():assert reuse(slot_generation=0,observed_generation=0,prior_frame=None,completed_frames=[])['status']=='REUSE_WITHIN_SCOPE'
def test_retired():assert reuse(slot_generation=1,observed_generation=1,prior_frame=0,completed_frames=[0,1])['status']=='REUSE_WITHIN_SCOPE'
def test_pending():assert reuse(slot_generation=1,observed_generation=1,prior_frame=0,completed_frames=[1])['status']=='WAIT_RETIREMENT'
def test_stale():assert reuse(slot_generation=2,observed_generation=1,prior_frame=0,completed_frames=[0])['status']=='STALE_GENERATION'

def test_rule_vuids_match_pinned_source():
 import json
 source=json.loads((pathlib.Path(__file__).resolve().parents[1]/'cases19/dynamic_ubo/normative.json').read_text())
 ids={x['vuid'] for x in source['entries']}
 for offsets in ([0],[1,16],[0,64]):assert set(bind(config(),offsets)['vuids'])<=ids
@pytest.mark.parametrize('key,value',[('maxUniformRange',1<<32),('bufferSize',1<<64)])
def test_config_width(key,value):
 m=config();m[key]=value
 with pytest.raises(ValueError):bind(m,[0,16])

def test_non_symmetric_oracle():
 a=[[int(x<1+(y%3)) for x in range(4)] for y in range(4)]
 assert a!=[list(x) for x in zip(*a)]
 assert a!=a[::-1]
 assert a!=[row[::-1] for row in a]
