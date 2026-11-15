import copy,importlib.util,pathlib,pytest
P=pathlib.Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('cases',P/'tools/resource_cases19.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def base():
 identity=dict(deviceType=4,apiVersion=4210993,vendorID=65541,deviceID=0,driverVersion=1,layerSpec=4210997,layerImplementation=1)
 index=dict(families=[dict(family='device_address',cpu_identity=identity,run_id='12345678-1234-1234-1234-123456789abc',status='BOUNDED_PHYSICAL_STORAGE_ADDRESS_PASS',artifacts={p:'a'*64 for p in ('summary.json','good.stdout','good.stderr','wrong-output.stdout','wrong-output.stderr','missing-usage.stdout','missing-usage.stderr')})],tests_head='b'*40,skill_head='c'*40,tool_hashes={'compiler':'a'*64},toolchain_sha256='f'*64,source_manifest={p:'d'*64 for p in ['cases19/device_address/'+f for f in ('probe.c','run.py','normative.json','compute.comp','capability_inventory.c')]+['tools/device_address19.py']})
 c=m.candidate(index,'device_address','e'*64);m.validate(c);return c
def reviewed():
 c=base();r=m.transition(c,'review','2026-11-15T00:00:00Z','independent-reviewer',dict(m.review_evidence(c['base']),review_report='3'*64),c['base']['scope'],'2026-11-20T00:00:00Z');m.validate(r);return r
def test_lifecycle():
 c=base();scope=c['base']['scope'];assert not m.retrieve([c],scope,'2026-11-16T00:00:00Z')['hits'];r=reviewed();assert m.retrieve([r],scope,'2026-11-16T00:00:00Z')['hits'];v=m.transition(r,'revoke','2026-11-17T00:00:00Z','reviewer2',{'decision_report':'4'*64},scope);assert v['history'][:1]==r['history'];assert not m.retrieve([v],scope,'2026-11-18T00:00:00Z')['hits'];assert not m.retrieve([r],scope,'2026-11-20T00:00:00Z')['hits']
@pytest.mark.parametrize('mutation',['scope','state','event','chain','delete','missing','bool','features','duplicate'])
def test_tamper(mutation):
 r=reviewed();assert m.retrieve([r],r['base']['scope'],'2026-11-16T00:00:00Z')['hits']
 if mutation=='scope':r['base']['scope']['cpu_identity']['deviceID']=7
 if mutation=='state':r['state']='candidate'
 if mutation=='event':r['history'][0]['reviewer']='changed'
 if mutation=='chain':r['history'][0]['previous']='a'*64
 if mutation=='delete':r['history']=[]
 if mutation=='missing':r['base']['scope'].pop('cpu_identity')
 if mutation=='bool':r['base']['scope']['cpu_identity']['deviceID']=True
 if mutation=='features':r['base']['scope']['required_feature_profile']=[]
 if mutation=='duplicate':
  with pytest.raises(ValueError):m.retrieve([r,r],r['base']['scope'],'2026-11-16T00:00:00Z')
  return
 with pytest.raises((ValueError,KeyError)):m.validate(r)
@pytest.mark.parametrize('change',['self-review','missing-counterexample','scope-elevation','expired','unknown'])
def test_invalid_review(change):
 c=base();scope=copy.deepcopy(c['base']['scope']);who='reviewer';ev=dict(m.review_evidence(c['base']),review_report='3'*64);expiry='2026-11-20T00:00:00Z';action='review'
 if change=='self-review':who=c['base']['author']
 if change=='missing-counterexample':ev.pop('counterexample_review')
 if change=='scope-elevation':scope['cpu_identity']['driverVersion']=99
 if change=='expired':expiry='2026-11-14T00:00:00Z'
 if change=='unknown':action='promote'
 with pytest.raises(ValueError):m.transition(c,action,'2026-11-15T00:00:00Z',who,ev,scope,expiry)
def test_revoked_cannot_review():
 r=reviewed();v=m.transition(r,'revoke','2026-11-17T00:00:00Z','reviewer2',{'decision_report':'4'*64},r['base']['scope'])
 with pytest.raises(ValueError):m.transition(v,'review','2026-11-18T00:00:00Z','reviewer3',dict(reproduction='1'*64,counterexample_review='2'*64,review_report='3'*64),v['base']['scope'],'2026-11-20T00:00:00Z')
def test_exact_scope_mismatch():
 r=reviewed();scope=copy.deepcopy(r['base']['scope']);scope['cpu_identity']['driverVersion']=2;assert m.retrieve([r],scope,'2026-11-16T00:00:00Z')['excluded'][0]['reason']=='scope mismatch'
def test_sanitized_no_raw_or_path():
 import json
 text=json.dumps(base());assert '/workspace' not in text and 'argv' not in text and 'address' not in text.replace('device_address','').replace('physical-storage-address-chain','').replace('bufferDeviceAddress','')
@pytest.mark.parametrize('change',['extra','absolute','traversal','rawtext','uuid','status','noevidence','authority','tool'])
def test_resigned_unsafe_candidate(change):
 c=base();b=c['base']
 if change=='extra':b['private']='secret'
 if change=='absolute':b['evidence'][0]['path']='/home/private/token'
 if change=='traversal':b['evidence'][0]['path']='device_address/../secret'
 if change=='rawtext':b['interpretation']='private contents'
 if change=='uuid':b['run_id']='private string'
 if change=='status':b['observed_status']='ALL_RELEASE_PASS'
 if change=='noevidence':b['evidence']=[]
 if change=='authority':b['authority']='new specification'
 if change=='tool':b['scope']['tool_cohort_sha256']=None
 c['id']=m.digest(b)
 with pytest.raises((ValueError,KeyError)):m.validate(c)
def test_unrelated_review_digest_rejected():
 c=base();ev=dict(m.review_evidence(c['base']),review_report='3'*64);ev['reproduction']='0'*64
 with pytest.raises(ValueError,match='not bound'):m.transition(c,'review','2026-11-15T00:00:00Z','reviewer',ev,c['base']['scope'],'2026-11-20T00:00:00Z')
def test_tool_scope_mismatch():
 r=reviewed();scope=copy.deepcopy(r['base']['scope']);scope['tool_cohort_sha256']='0'*64;assert not m.retrieve([r],scope,'2026-11-16T00:00:00Z')['hits']
def cli_module():
 spec=importlib.util.spec_from_file_location('build_cases',P/'checks19/build_resource_cases.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def test_duplicate_json_keys(tmp_path):
 mod=cli_module();p=tmp_path/'duplicate.json';p.write_text('{"state":"candidate","state":"reviewed"}')
 with pytest.raises(ValueError,match='duplicate'):mod.parse(p)
def test_cli_stale_anchor_no_output(tmp_path,monkeypatch):
 import sys
 mod=cli_module();inp=tmp_path/'input.json';inp.write_text('{}');req=tmp_path/'request.json';req.write_text('{}');out=tmp_path/'out.json'
 monkeypatch.setattr(mod,'checked',lambda *a:None);monkeypatch.setattr(mod,'git',lambda *a:b'a'*40)
 monkeypatch.setattr(sys,'argv',['entry','--output',str(out),'retrieve','--input',str(inp),'--expected-input-sha256','0'*64,'--request',str(req)])
 assert mod.main()==1;assert not out.exists();assert inp.read_text()=='{}'
def test_cli_refuses_overwrite(tmp_path,monkeypatch):
 import sys
 mod=cli_module();inp=tmp_path/'input.json';inp.write_text('{"untouched":true}');req=tmp_path/'request.json';req.write_text('{}')
 monkeypatch.setattr(sys,'argv',['entry','--output',str(inp),'retrieve','--input',str(inp),'--expected-input-sha256',mod.sha(inp),'--request',str(req)])
 assert mod.main()==1;assert inp.read_text()=='{"untouched":true}'
@pytest.mark.parametrize('missing',['cases19/device_address/probe.c','device_address/good.stderr','device_address/summary.json','device_address/missing-usage.stdout'])
def test_required_evidence_cannot_be_dropped(missing):
 c=base();c['base']['evidence']=[e for e in c['base']['evidence'] if e['path']!=missing];c['id']=m.digest(c['base'])
 with pytest.raises(ValueError,match='evidence missing'):m.validate(c)
