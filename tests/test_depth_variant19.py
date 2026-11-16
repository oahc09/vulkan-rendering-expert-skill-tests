import importlib.util,pathlib,sys,copy,pytest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import depth_variant19 as r
@pytest.fixture
def records():
 out={}
 for name,key in {'output':'image_allocation','sampled_source':'source_allocation','depth':'depth_allocation','readback':'buffer_allocation'}.items():
  out[key]=dict(size=16,selectedType=0);out[name+'_request']=dict(kind=name+'_request',object=name,requestedBytes=16,memoryTypeIndex=0)
 out['allocation_budget']=dict(kind='allocation_budget',samples=1,allocationCount=4,requestedBytes=64,residentBytesKnown=False,driverInternalBytesKnown=False,performanceKnown=False)
 assert r.allocations(1,out)['total_requested_bytes']==64
 return out
@pytest.mark.parametrize('field,value',[('requestedBytes',True),('requestedBytes',-1),('requestedBytes',2**64),('memoryTypeIndex',32)])
def test_bad_receipt(records,field,value):
 records['output_request'][field]=value
 with pytest.raises(ValueError):r.allocations(1,records)
def test_no_unused(records):
 records['multi_allocation']={}
 with pytest.raises(ValueError):r.allocations(1,records)
def test_sum(records):
 records['allocation_budget']['requestedBytes']=65
 with pytest.raises(ValueError):r.allocations(1,records)
def test_missing(records):
 del records['depth_request']
 with pytest.raises(ValueError):r.allocations(1,records)
def test_missing_metric(records):
 del records['allocation_budget']['performanceKnown']
 with pytest.raises(ValueError):r.allocations(1,records)
def test_variant():
 m=dict(sourceSamples=1,resolveSamples=1,sourceFormat=37,resolveFormat=37,resolveMode=0,sourceLayout=1,resolveLayout=0,storeOp=0,distinctImages=True,sampledResolveView=True,sourcePipelineSamples=1,sourceSampleShading=0,postPipelineSamples=1);f=dict(format=37,usage=21,samples=1,supportedSamples=1,maxWidth=4,maxHeight=4,maxLayers=1);c=dict(colorSampleCounts=1)
 assert r.topology(1,m,f,c) # 1x does not require 4x support
 m['resolveMode']=2;assert not r.topology(1,m,f,c)

def test_extra_receipt(records):
 records['extra_request']=dict(kind='extra_request',object='extra',requestedBytes=16,memoryTypeIndex=0);records['extra_allocation']=dict(size=16,selectedType=0)
 with pytest.raises(ValueError,match='unexpected'):r.allocations(1,records)
