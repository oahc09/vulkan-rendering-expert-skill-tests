import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.indirect_draw19 import admit,content,PREFIX

def config():return dict(multiDrawSupported=1,firstInstanceSupported=1,size=32,usage=288,offset=0,count=1,stride=16,maxDrawIndirectCount=16,multiDrawEnabled=False,firstInstanceEnabled=False)
def test_good():assert admit(config())['vuids']==[]
@pytest.mark.parametrize('key,val,ids',[('offset',2,['offset-02710']),('usage',32,['buffer-02709']),('size',15,['drawCount-00487']),('count',2,['drawCount-02718']),('maxDrawIndirectCount',0,['drawCount-02719'])])
def test_bad(key,val,ids):
 m=config();m[key]=val;assert admit(m)['vuids']==[PREFIX+x for x in ids]
def test_zero_no_range_stride():
 m=config();m.update(count=0,size=0,offset=100,stride=3);assert admit(m)['vuids']==[]
def test_one_ignores_stride():
 m=config();m['stride']=3;assert admit(m)['vuids']==[]
def test_multi_stride_range():
 m=config();m.update(count=3,multiDrawEnabled=True,stride=18);assert admit(m)['vuids']==[PREFIX+'drawCount-00476',PREFIX+'drawCount-00488']
def test_unknown():assert admit({})['status']=='UNKNOWN'
@pytest.mark.parametrize('k,v',[('offset',True),('count',-1),('firstInstanceEnabled',1)])
def test_types(k,v):
 m=config();m[k]=v
 with pytest.raises(ValueError):admit(m)
def test_content():assert content([3,1,0,0],first_instance_enabled=False)['status']=='CONTENT_WITHIN_SCOPE'
def test_firstinstance():assert content([3,1,0,1],first_instance_enabled=False)['status']=='REJECTED_FIRST_INSTANCE'
def test_unknown_content():assert content(None,first_instance_enabled=False)['status']=='UNKNOWN'
def test_overflow():
 with pytest.raises(ValueError):content([1<<32,1,0,0],first_instance_enabled=False)

@pytest.mark.parametrize('key,val',[('offset',1<<64),('size',1<<64),('count',1<<32),('stride',1<<32),('usage',1<<32),('maxDrawIndirectCount',1<<32),('offset',(1<<64)-4)])
def test_overwide(key,val):
 m=config();m[key]=val
 with pytest.raises(ValueError):admit(m)
def test_inconsistent_support():
 m=config();m.update(multiDrawSupported=0,multiDrawEnabled=True);assert admit(m)['status']=='UNKNOWN'
