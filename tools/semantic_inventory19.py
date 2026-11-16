"""Partial frozen semantic-review inventory. Indexing is NEVER L1/L2 acceptance.
309 VUID clause coordinates and 368 Registry scopes are separate denominators.
Human assertions/review identities are declarations, not authenticated proofs.
"""
import argparse,hashlib,json,re
from pathlib import Path
try:
 from . import diagnostic_spec19 as spec
 from . import core17_registry_inventory as registry
except ImportError:
 import diagnostic_spec19 as spec
 import core17_registry_inventory as registry

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def hexsha(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
def token(value):return isinstance(value,str) and re.fullmatch('[A-Za-z0-9_.:-]{1,160}',value) is not None
def anchor(value):
 if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_./-]+\.md#[A-Za-z0-9_-]+',value):return False
 path=value.split('#')[0]
 return not path.startswith('/') and all(p not in ('','.','..') for p in path.split('/'))
def exact(value,keys,name):require(isinstance(value,dict) and set(value)==set(keys),'exact '+name+' schema required')

def _assemble(corpus,reg):
 """Pure constructor, for tests; public load requires both exact pinned byte hashes."""
 units={}
 for rows in corpus['entries'].values():
  for entry in rows:
   facts={**entry,'spec_source_sha256':corpus['source']['sha256'],'spec_api_version':corpus['source']['api_version']}
   entry_sha=digest(facts);unit_id='vu:'+entry_sha
   require(unit_id not in units,'duplicate normative unit')
   units[unit_id]={'unit_id':unit_id,'entry_sha256':entry_sha,**facts,'semantic_status':'UNREVIEWED'}
 scopes={};excluded=[]
 for kind,records in (('feature',reg['features']),('extension',reg['extensions'])):
  for row in records:
   included=row['included_standard_vulkan'] if kind=='feature' else row['classification']=='vulkan_stable'
   binding={'registry_source_sha256':reg['source_sha256'],'kind':kind,'name':row['name'],'record_sha256':digest(row)}
   scope_id='scope:'+digest(binding)
   if included:
    require(scope_id not in scopes,'duplicate scope');scopes[scope_id]={**binding,'scope_id':scope_id,'registry_api_version':'1.4.368','record':row,'semantic_status':'UNREVIEWED'}
   else:excluded.append({**binding,'reason':row.get('classification','not_standard_vulkan_1_0_to_1_4'),'api':row.get('api',row.get('supported')),'sc_independent': 'vulkansc' in (row.get('api',row.get('supported')) or '')})
 return {'schema':1,'status':'PARTIAL_FROZEN_REVIEW_INVENTORY','sources':{'normative':corpus['source'],'registry':{'sha256':reg['source_sha256'],'commit':reg['source_commit'],'api_version':'1.4.368'}},'denominators':{'unique_vuids':corpus['statistics']['unique_vuids'],'normative_owner_condition_units':len(units),'stable_registry_review_scopes':len(scopes),'included_feature_scopes':sum(s['kind']=='feature' for s in scopes.values()),'included_extension_scopes':sum(s['kind']=='extension' for s in scopes.values())},'units':dict(sorted(units.items())),'scopes':dict(sorted(scopes.items())),'excluded_registry_records':sorted(excluded,key=lambda x:(x['kind'],x['name'])),'normative_statistics':corpus['statistics'],'limitations':['VUID coordinates are only a normative sub-denominator, not all semantic facts.','Registry 1.4.368 and validusage 1.4.309 remain separate; mapping is a manual applicability declaration, not version equivalence.','No complete video.xml, specification prose, reference pages, Headers, SPIR-V or tool semantic denominator.','No transitive member/enum/alias/pNext/dependency semantic closure; existing Registry inventory limitations apply.','No automatic applicability reasoning, natural-language contradiction detection or L0/L1/L2 acceptance.','SC and provisional/disabled/other-API entries remain separate; exclusions here are not waivers of the original plan.']}

def load(validusage_raw,registry_raw):
 corpus=spec.load_pinned(validusage_raw)
 require(hashlib.sha256(registry_raw).hexdigest()==registry.SOURCE_SHA256,'wrong frozen Registry bytes')
 reg=registry.inventory(registry_raw);result=_assemble(corpus,reg)
 require(result['denominators']['stable_registry_review_scopes']==497 and result['denominators']['included_feature_scopes']==20 and result['denominators']['included_extension_scopes']==477,'frozen scope denominator changed')
 return result

CLAIM_KEYS={'claim_id','unit_id','entry_sha256','scope','predicate','assertion','card_anchor','card_sha256','authority_anchor','authority_sha256','version_mapping'}
SCOPE_KEYS={'registry_scope_id','registry_record_sha256','normative_api_version','registry_api_version','api_variant','platform','profile','enabled_features'}
REVIEW_KEYS={'review_id','claim_id','claim_sha256','reviewer','outcome','declared_level','evidence_sha256','version_applicability'}
def validate_claim(inv,claim):
 exact(claim,CLAIM_KEYS,'claim');require(token(claim['claim_id']) and token(claim['predicate']),'claim/predicate identity');require(type(claim['assertion']) is bool,'boolean assertion required')
 unit=inv['units'].get(claim['unit_id']);require(unit is not None and claim['entry_sha256']==unit['entry_sha256'],'missing/stale normative coordinate')
 require(anchor(claim['card_anchor']) and anchor(claim['authority_anchor']) and hexsha(claim['card_sha256']) and hexsha(claim['authority_sha256']),'card/authority binding')
 require(claim['version_mapping']=='MANUAL_309_CLAUSE_TO_368_SCOPE','explicit version bridge required')
 scope=claim['scope'];exact(scope,SCOPE_KEYS,'scope');registered=inv['scopes'].get(scope['registry_scope_id']);require(registered is not None and scope['registry_record_sha256']==registered['record_sha256'],'missing/stale registry scope')
 require(scope['normative_api_version']=='1.4.309' and scope['registry_api_version']=='1.4.368' and scope['api_variant']=='Vulkan','version/API scopes must remain separate')
 require(token(scope['platform']) and token(scope['profile']),'explicit platform/profile required')
 features=scope['enabled_features'];require(isinstance(features,list) and all(token(x) for x in features) and features==sorted(set(features)),'explicit sorted feature assumptions required')
 return digest(claim)

def audit(inv,claims,reviews):
 require(isinstance(claims,list) and isinstance(reviews,list),'claim/review arrays required')
 by_id={};bindings={};findings=[];groups={};predicate_groups={};coordinates={}
 for claim in claims:
  claim_sha=validate_claim(inv,claim);cid=claim['claim_id'];require(cid not in by_id,'duplicate claim ID');by_id[cid]=claim;bindings[cid]=claim_sha
  scope_sha=digest({'declared_scope':claim['scope'],'normative_condition':inv['units'][claim['unit_id']]['condition_key']});key=(scope_sha,claim['predicate']);groups.setdefault(key,[]).append(claim);predicate_groups.setdefault(claim['predicate'],[]).append(claim)
  coordinate=(claim['unit_id'],scope_sha,claim['predicate'],claim['card_anchor'])
  if coordinate in coordinates:findings.append({'kind':'DUPLICATE_CLAIM_COORDINATE','claims':sorted([coordinates[coordinate],cid])})
  else:coordinates[coordinate]=cid
 for (scope_sha,predicate),rows in sorted(groups.items()):
  ids=sorted(x['claim_id'] for x in rows)
  if len({x['assertion'] for x in rows})>1:findings.append({'kind':'SAME_SCOPE_OPPOSED_ASSERTIONS','predicate':predicate,'scope_sha256':scope_sha,'claims':ids,'meaning':'Explicit structured declarations conflict; prose truth not adjudicated.'})
  if len({(x['authority_anchor'],x['authority_sha256']) for x in rows})>1:findings.append({'kind':'MULTIPLE_AUTHORITY_BINDINGS','predicate':predicate,'scope_sha256':scope_sha,'claims':ids})
 for predicate,rows in sorted(predicate_groups.items()):
  for i,left in enumerate(sorted(rows,key=lambda x:x['claim_id'])):
   for right in sorted(rows,key=lambda x:x['claim_id'])[i+1:]:
    if left['assertion']!=right['assertion'] and (left['scope']!=right['scope'] or inv['units'][left['unit_id']]['condition_key']!=inv['units'][right['unit_id']]['condition_key']):findings.append({'kind':'DIFFERENT_SCOPE_OPPOSITION_NEEDS_APPLICABILITY_REVIEW','predicate':predicate,'claims':[left['claim_id'],right['claim_id']],'is_established_contradiction':False})
 review_ids=set();reviewed={}
 for review in reviews:
  exact(review,REVIEW_KEYS,'review');rid=review['review_id'];require(token(rid) and rid not in review_ids,'missing/duplicate review ID');review_ids.add(rid)
  cid=review['claim_id'];require(cid in by_id and review['claim_sha256']==bindings[cid],'missing/stale review claim binding');require(token(review['reviewer']),'declared reviewer required')
  require(review['outcome'] in ('ACCEPTED_DECLARATION','REJECTED','NEEDS_REVIEW') and review['declared_level'] in ('L1','L2'),'review outcome/level')
  evidence=review['evidence_sha256'];require(isinstance(evidence,list) and len(evidence)>0 and all(hexsha(x) for x in evidence) and evidence==sorted(set(evidence)),'review evidence digests required')
  require(review['version_applicability'] in ('REVIEWER_DECLARED_APPLICABLE','UNRESOLVED'),'version applicability')
  if review['outcome']=='ACCEPTED_DECLARATION':require(review['version_applicability']=='REVIEWER_DECLARED_APPLICABLE','unresolved cross-version review cannot be accepted declaration')
  reviewed.setdefault(cid,[]).append(review)
 for cid,rows in sorted(reviewed.items()):
  if len({r['outcome'] for r in rows})>1:findings.append({'kind':'CONFLICTING_REVIEW_DECLARATIONS','claim_id':cid,'reviews':sorted(r['review_id'] for r in rows)})
 claimed_units={c['unit_id'] for c in claims};claimed_scopes={c['scope']['registry_scope_id'] for c in claims}
 # Acceptance is a caller declaration, not adjudication. Any unresolved audit
 # finding conservatively blocks the affected claim from the uncontested view.
 declared_accepted=sorted(cid for cid,rs in reviewed.items() if any(r['outcome']=='ACCEPTED_DECLARATION' for r in rs))
 blocked=set()
 for finding in findings:
  blocked.update(finding.get('claims',[]))
  if 'claim_id' in finding:blocked.add(finding['claim_id'])
 uncontested=sorted(cid for cid in declared_accepted if cid not in blocked and {r['outcome'] for r in reviewed[cid]}=={'ACCEPTED_DECLARATION'})
 return {'schema':1,'status':'DECLARATION_AUDIT_ONLY','inventory_sources':inv['sources'],'denominators':inv['denominators'],'claim_bindings':dict(sorted(bindings.items())),'findings':findings,'counts':{'claims':len(claims),'review_declarations':len(reviews),'unclaimed_normative_units':len(inv['units'])-len(claimed_units),'unclaimed_registry_scopes':len(inv['scopes'])-len(claimed_scopes),'claims_without_review':len(set(by_id)-set(reviewed))},'unclaimed_normative_unit_ids':sorted(set(inv['units'])-claimed_units),'unclaimed_registry_scope_ids':sorted(set(inv['scopes'])-claimed_scopes),'claims_without_review':sorted(set(by_id)-set(reviewed)),'declared_accepted':declared_accepted,'conflict_blocked_claims':sorted(blocked),'uncontested_accepted_review_declarations':uncontested,'accepted_review_declarations':uncontested,'semantic_L1_L2_completion':'UNKNOWN_NOT_INFERRED','release_status':'BLOCKED','review_authority':'Caller-declared identity/evidence digest only; not authentication or verification of evidence contents.','limits':['Accepted lists exclude every unresolved audit finding; declared_accepted preserves caller assertions, not verified evidence.','No accepted declaration completes a VUID, feature, extension or domain automatically.','Assertions are caller-structured predicates, not automatic extraction of natural-language meaning.','Different scopes are not merged or evaluated for implication.','Hash binding detects changes relative to supplied records, not reviewer authenticity.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--validusage',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--claims',type=Path);p.add_argument('--reviews',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 inv=load(a.validusage.read_bytes(),a.registry.read_bytes());claims=spec.parse_json(a.claims.read_bytes()) if a.claims else [];reviews=spec.parse_json(a.reviews.read_bytes()) if a.reviews else [];report=audit(inv,claims,reviews)
 a.out.mkdir(parents=True,exist_ok=False)
 for name,data in (('inventory',inv),('audit',report)):(a.out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'denominators':inv['denominators'],'counts':report['counts'],'semantic_L1_L2_completion':report['semantic_L1_L2_completion']}))
if __name__=='__main__':main()
