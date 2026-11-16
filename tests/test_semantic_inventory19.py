"""Small mechanical fixtures; tests do not assert real L1/L2 completion."""
import copy,hashlib,json,pytest
from tools import semantic_inventory19 as m
from tools import diagnostic_spec19 as s
from tools import core17_registry_inventory as reg
@pytest.fixture
def inv():
 doc={'version info':{'schema version':2,'api version':'1.4.309'},'validation':{'vkExample':{'core':[{'vuid':'VUID-vkExample-value-00001','text':'Must hold','page':'example.html'}],'FEATURE_X':[{'vuid':'VUID-vkExample-value-00001','text':'Conditional must hold','page':'example.html'}]}}}
 corpus=s.index_document(doc);corpus['source']={'sha256':s.PINNED_SHA256,'api_version':'1.4.309'}
 row={'name':'VK_VERSION_1_0','api':'vulkan','included_standard_vulkan':True,'requirements':[],'semantic_L1_L2':'UNREVIEWED'}
 registry={'source_sha256':reg.SOURCE_SHA256,'source_commit':reg.SOURCE_COMMIT,'features':[row], 'extensions':[{'name':'VK_FAKE_example','classification':'vulkan_stable','supported':'vulkan','requirements':[],'semantic_L1_L2':'UNREVIEWED'},{'name':'VK_FAKE_sc','classification':'other_api_or_unspecified','supported':'vulkansc'}]}
 return m._assemble(corpus,registry)
@pytest.fixture
def claim(inv):
 u=next(iter(inv['units'].values()));scope=next(iter(inv['scopes'].values()))
 c={'claim_id':'c1','unit_id':u['unit_id'],'entry_sha256':u['entry_sha256'],'scope':{'registry_scope_id':scope['scope_id'],'registry_record_sha256':scope['record_sha256'],'normative_api_version':'1.4.309','registry_api_version':'1.4.368','api_variant':'Vulkan','platform':'portable','profile':'ordinary','enabled_features':[]},'predicate':'example.must-hold','assertion':True,'card_anchor':'references/example.md#rule','card_sha256':'1'*64,'authority_anchor':'references/example.md#rule','authority_sha256':'1'*64,'version_mapping':'MANUAL_309_CLAUSE_TO_368_SCOPE'}
 assert m.validate_claim(inv,c)==m.digest(c)
 return c
def review(c):return {'review_id':'r1','claim_id':c['claim_id'],'claim_sha256':m.digest(c),'reviewer':'declared-reviewer','outcome':'ACCEPTED_DECLARATION','declared_level':'L1','evidence_sha256':['2'*64],'version_applicability':'REVIEWER_DECLARED_APPLICABLE'}
def test_conditional_coordinates(inv):
 assert inv['denominators']['unique_vuids']==1 and inv['denominators']['normative_owner_condition_units']==2
 assert len({u['condition_key'] for u in inv['units'].values()})==2
 assert inv['excluded_registry_records'][0]['sc_independent'] is True
 assert inv['units']==dict(sorted(inv['units'].items()))
def test_empty_not_complete(inv):
 a=m.audit(inv,[],[]);assert a['counts']['unclaimed_registry_scopes']==2 and a['semantic_L1_L2_completion']=='UNKNOWN_NOT_INFERRED'
def test_accepted_not_scope_complete(inv,claim):
 a=m.audit(inv,[claim],[review(claim)]);assert a['accepted_review_declarations']==['c1'] and a['semantic_L1_L2_completion']=='UNKNOWN_NOT_INFERRED' and a['release_status']=='BLOCKED'
def test_same_scope_opposition(inv,claim):
 c=copy.deepcopy(claim);c.update(claim_id='c2',assertion=False)
 a=m.audit(inv,[claim,c],[]);assert any(f['kind']=='SAME_SCOPE_OPPOSED_ASSERTIONS' for f in a['findings'])
def test_different_scope_not_contradiction(inv,claim):
 c=copy.deepcopy(claim);c.update(claim_id='c2',assertion=False);c['scope']['enabled_features']=['differentFeature']
 f=m.audit(inv,[claim,c],[])['findings'];assert not any(x['kind']=='SAME_SCOPE_OPPOSED_ASSERTIONS' for x in f)
 assert any(x['kind']=='DIFFERENT_SCOPE_OPPOSITION_NEEDS_APPLICABILITY_REVIEW' and x['is_established_contradiction'] is False for x in f)
def test_authority_conflict(inv,claim):
 c=copy.deepcopy(claim);c.update(claim_id='c2',authority_anchor='other.md#rule');assert any(x['kind']=='MULTIPLE_AUTHORITY_BINDINGS' for x in m.audit(inv,[claim,c],[])['findings'])
def test_duplicate_coordinate(inv,claim):
 c=copy.deepcopy(claim);c['claim_id']='c2';assert any(x['kind']=='DUPLICATE_CLAIM_COORDINATE' for x in m.audit(inv,[claim,c],[])['findings'])
def test_duplicate_id(inv,claim):
 with pytest.raises(ValueError,match='duplicate claim'):m.audit(inv,[claim,claim],[])
@pytest.mark.parametrize('field,value',[('unit_id','unknown'),('entry_sha256','0'*64),('assertion',1),('card_anchor','../secret.md#x'),('card_anchor','/etc/private.md#x'),('card_sha256','unknown'),('version_mapping','AUTO_EQUIVALENT'),('authority_anchor','https://example.com/a.md#x')])
def test_bad_claim(inv,claim,field,value):
 claim[field]=value
 with pytest.raises(ValueError):m.audit(inv,[claim],[])
@pytest.mark.parametrize('field,value',[('api_variant','VulkanSC'),('normative_api_version','1.4.368'),('registry_api_version','1.4.309'),('registry_scope_id','unknown'),('registry_record_sha256','0'*64),('enabled_features',['z','a']),('enabled_features',['a','a']),('profile','')])
def test_bad_scope(inv,claim,field,value):
 claim['scope'][field]=value
 with pytest.raises(ValueError):m.audit(inv,[claim],[])
@pytest.mark.parametrize('field,value',[('claim_sha256','0'*64),('claim_id','missing'),('evidence_sha256',[]),('evidence_sha256',['not-hash']),('version_applicability','UNRESOLVED'),('outcome','AUTO_VERIFIED'),('declared_level','E_PASS')])
def test_bad_review(inv,claim,field,value):
 r=review(claim);r[field]=value
 with pytest.raises(ValueError):m.audit(inv,[claim],[r])
def test_conflicting_review_declarations(inv,claim):
 a=review(claim);b=review(claim);b.update(review_id='r2',outcome='REJECTED')
 assert any(f['kind']=='CONFLICTING_REVIEW_DECLARATIONS' for f in m.audit(inv,[claim],[a,b])['findings'])
def test_duplicate_review(inv,claim):
 r=review(claim)
 with pytest.raises(ValueError,match='review ID'):m.audit(inv,[claim],[r,r])
def test_wrong_corpus_digest():
 with pytest.raises(ValueError,match='digest mismatch'):m.load(b'{}',b'garbage')
def test_duplicate_json():
 with pytest.raises(ValueError,match='duplicate'):s.parse_json('{"x":1,"x":2}')
def test_text_is_data(inv):
 # No evaluation/HTML rendering is offered; original exact text retained.
 assert any(u['text_html']=='Must hold' for u in inv['units'].values())

def test_different_normative_condition_not_merged(inv,claim):
 c=copy.deepcopy(claim);u=next(u for u in inv['units'].values() if u['unit_id']!=claim['unit_id']);c.update(claim_id='c2',unit_id=u['unit_id'],entry_sha256=u['entry_sha256'],assertion=False)
 findings=m.audit(inv,[claim,c],[])['findings']
 assert not any(f['kind']=='SAME_SCOPE_OPPOSED_ASSERTIONS' for f in findings)
 assert any(f['kind']=='DIFFERENT_SCOPE_OPPOSITION_NEEDS_APPLICABILITY_REVIEW' for f in findings)

@pytest.mark.parametrize('mutation',[{'assertion':False},{'authority_anchor':'other.md#rule'}])
def test_conflicted_acceptance_filtered(inv,claim,mutation):
 c=copy.deepcopy(claim);c.update(claim_id='c2',card_anchor='other.md#claim',**mutation)
 r=review(c);r['review_id']='r2'
 a=m.audit(inv,[claim,c],[review(claim),r])
 assert a['declared_accepted']==['c1','c2']
 assert a['conflict_blocked_claims']==['c1','c2']
 assert a['accepted_review_declarations']==a['uncontested_accepted_review_declarations']==[]

def test_uncontested_acceptance_preserved(inv,claim):
 a=m.audit(inv,[claim],[review(claim)])
 assert a['declared_accepted']==a['uncontested_accepted_review_declarations']==['c1']
 assert a['conflict_blocked_claims']==[]

def test_conflicting_reviews_keep_declaration_not_acceptance(inv,claim):
 r=review(claim);r.update(review_id='r2',outcome='REJECTED')
 a=m.audit(inv,[claim],[review(claim),r])
 assert a['declared_accepted']==['c1'] and a['conflict_blocked_claims']==['c1']
 assert a['accepted_review_declarations']==[]
