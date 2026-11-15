import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import scale_choice19 as r
pytestmark=pytest.mark.candidate19
F=json.loads((ROOT/'tests/fixtures/scale-choice19.json').read_text())
def test_complete_actual_shapes():
 for label,path,mode in [('baseline','direct','good'),('indirect','indirect','good'),('recovery','direct','good'),('direct-wrong','direct','wrong-output'),('indirect-wrong','indirect','wrong-output'),('limited-count','indirect','limited-count')]:r.check(F[label],path,mode)
 assert r.check(F['baseline'],'direct')==r.check(F['recovery'],'direct')
@pytest.mark.parametrize('kind,key,value',[('scale_config','countEnabled',0),('scale_config','countSupported',0),('scale_config','stride',12),('scale_config','maxDrawCount',17),('scale_config','countOffset',257),('scale_config','maxDrawIndirectCount',6),('binding_facts','outputRange',256),('binding_facts','outputIsCommands',0),('binding_facts','dispatch',[0,1,1]),('organization','drawCalls',False),('execution','fenceCompleted',False),('indirect_dependency','dstAccess',0),('argument_retirement_dependency','dstAccess',0),('scale_allocation','selectedFlags',1),('final','rc',0.0)])
def test_coordinated_bad_facts(kind,key,value):
 r.check(F['indirect'],'indirect');a=copy.deepcopy(F['indirect']);next(x for x in a if x['kind']==kind)[key]=value
 with pytest.raises(ValueError):r.check(a,'indirect')
@pytest.mark.parametrize('index,value',[(0,3),(2,6),(28,1),(64,6),(65,1),(67,True)])
def test_command_tamper(index,value):
 a=copy.deepcopy(F['indirect']);next(x for x in a if x['kind']=='commands')['values'][index]=value
 with pytest.raises(ValueError):r.check(a,'indirect')
def test_truncation_not_accepted_good():
 with pytest.raises(ValueError):r.check(F['limited-count'],'indirect')
def test_policy_not_automatic_gpu():
 assert r.decide(F['baseline'],F['indirect'],7)['status']=='KEEP_BASELINE'
 assert r.decide(F['baseline'],F['indirect'],1)['status']=='NEEDS_COMPARABLE_BASELINE'
 assert r.decide(F['baseline'],F['indirect'],7,True)['status']=='NEEDS_MEASUREMENT'
@pytest.mark.parametrize('bad',[None,[],{},True])
def test_fake_status(bad):assert r.decide(bad,F['indirect'])['status']=='UNKNOWN'
def test_order():
 a=copy.deepcopy(F['indirect']);w=next(x for x in a if x['kind']=='commands')['values'];w[0:4],w[4:8]=w[4:8],w[0:4]
 with pytest.raises(ValueError):r.check(a,'indirect')
