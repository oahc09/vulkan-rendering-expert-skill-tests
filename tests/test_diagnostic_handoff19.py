"""Portable handoff controls: byte integrity is not a Vulkan rerun."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('handoff',ROOT/'tools/diagnostic_handoff19.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
s=importlib.util.spec_from_file_location('handoffcli',ROOT/'checks19/build_diagnostic_handoff.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def package(root):
 root.mkdir();files={};h.add_artifact(root,'evidence/raw.log',b'observed\n',files,{'kind':'test'})
 raw=json.dumps({'schema_version':1,'status':'VERIFIED_READING_PACKAGE','files':files}).encode();(root/'handoff-manifest.json').write_bytes(raw);return h.digest(raw)
def test_package_bytes_only(tmp_path):
 digest=package(tmp_path/'p');r=h.verify_package(tmp_path/'p',digest,c.parse)
 assert r['status']=='PACKAGE_BYTES_VERIFIED_ONLY' and 'execution' in r['not_verified']
@pytest.mark.parametrize('mutation',['alter','missing','extra','manifest','symlink'])
def test_package_tampering_rejected(tmp_path,mutation):
 root=tmp_path/'p';digest=package(root)
 if mutation=='alter':(root/'evidence/raw.log').write_text('different')
 elif mutation=='missing':(root/'evidence/raw.log').unlink()
 elif mutation=='extra':(root/'unknown.txt').write_text('extra')
 elif mutation=='manifest':(root/'handoff-manifest.json').write_text('{}')
 else:(root/'link').symlink_to(root/'evidence/raw.log')
 with pytest.raises(ValueError):h.verify_package(root,digest,c.parse)
def test_symlink_root_rejected(tmp_path):
 root=tmp_path/'p';digest=package(root);link=tmp_path/'link';link.symlink_to(root,target_is_directory=True)
 with pytest.raises(ValueError):h.verify_package(link,digest,c.parse)
@pytest.mark.parametrize('path',['/absolute','../escape','a/../../escape','C:\\secret','a\\b','https://evil'])
def test_bad_portable_paths(path):
 with pytest.raises(ValueError):h.safe_relative(path)
@pytest.mark.parametrize('text',['/tmp/private','/workspace/private','/home/agent/private','C:\\private','x\x00y'])
def test_private_paths_or_binary_rejected(text):
 with pytest.raises(ValueError):h.check_portable_text(text.encode())
def test_manifest_requires_external_trust_digest(tmp_path):
 root=tmp_path/'p';package(root)
 with pytest.raises(ValueError):h.verify_package(root,'',c.parse)
def test_duplicate_manifest_key_rejected():
 with pytest.raises(ValueError):c.parse('{"status":1,"status":2}')
def test_no_executable_in_allowlist():
 assert h.source_allowlist() and all(Path(x).suffix in ('.c','.comp','.patch') for x in h.source_allowlist())
def test_escaping_normative_text():
 assert '`' not in h.inline('`[click](javascript:x)<script>') and '<script>' not in h.inline('`[click](javascript:x)<script>')
def actual_reports():
 names={'transfer':'transfer-case','descriptor_lifetime':'descriptor-lifetime','pipeline_interface':'pipeline-interface','image_compute':'image-compute','tool_capture':'local-tools'}
 return {key:json.loads((ROOT/'coverage/v1.0.19'/(name+'.json')).read_text()) for key,name in names.items()}
@pytest.mark.parametrize('language',['zh','en'])
def test_honest_narrative_classifies_abort_oracle_and_unsubmitted(language):
 text=h.triage({'tests_head':'a'*40,'skill_head':'b'*40,'run_id':'11111111-1111-4111-8111-111111111111'},actual_reports(),{'observations':[]},language)
 assert 'pipeline_result=-1000011001' in text and 'submitted=false' in text
 assert 'unsubmitted pixel placeholders (not GPU output)' in text
 assert 'oracle negative' in text and 'noncoherent' in text
 assert 'final' in text.lower() or '最终' in text
 assert 'external production bug' in text or '不是外部生产工程' in text
def test_raw_allowlist_excludes_commands_and_full_summaries():
 paths=h.raw_allowlist(actual_reports())
 assert paths and all('summary' not in p and 'build' not in p and not p.endswith('.spv') for p in paths)
def test_wrong_checkout_rejected(tmp_path):
 with pytest.raises(ValueError):c.checked_dependencies(tmp_path,'a'*40,development=True)
def test_uncommitted_dependency_rejected_before_import(monkeypatch):
 monkeypatch.setattr(c,'git',lambda root,*args:('a'*40).encode() if args[0]=='rev-parse' else b'wrong committed bytes')
 monkeypatch.setattr(c,'load_module',lambda *args:pytest.fail('unverified dependency executed'))
 with pytest.raises(ValueError,match='dependency not'):c.checked_dependencies(c.ROOT,'a'*40)
def test_recomputed_normative_report_not_optional(monkeypatch,tmp_path):
 # Real verification must precede copying; a failure never creates a successful package.
 root=tmp_path/'output';bundle=tmp_path/'bundle';bundle.mkdir();(bundle/'delivery-index.json').write_text(json.dumps({'tests_head':'a'*40}))
 class Args:pass
 a=Args();a.output=root;a.bundle=bundle;a.tests_root=c.ROOT;a.development=False
 monkeypatch.setattr(c,'checked_dependencies',lambda *args:(_ for _ in ()).throw(ValueError('forged normative pairing')))
 assert c.build(a)==1
 receipt=json.loads((root/'handoff-receipt.json').read_text());assert receipt['status']=='BLOCKED' and not (root/'handoff/handoff-manifest.json').exists()
def test_run_id_markdown_injection_rejected():
 with pytest.raises(ValueError):h.triage({'tests_head':'a'*40,'skill_head':'b'*40,'run_id':'x`\n<img src=x onerror=alert(1)>\n`'},actual_reports(),{'observations':[]},'zh')
def test_phase_and_normative_page_escaped():
 index={'tests_head':'a'*40,'skill_head':'b'*40,'run_id':'11111111-1111-4111-8111-111111111111'}
 event={'chain':'transfer','case':'before','phase':'`<script>','line':1,'logfile':'transfer/before.log','diagnostic':'VUID-safe'}
 norm={'observations':[{'observation':event,'lookup':{'status':'MATCHED_SPEC_ENTRY','normative_entries':[{'api_owner':'owner','condition_key':'`<img>','page':'`<script>'}]}}]}
 text=h.triage(index,actual_reports(),norm,'en')
 assert '<script>' not in text and '<img>' not in text and '&lt;script&gt;' in text
def test_final_verification_failure_never_publishes_success(monkeypatch,tmp_path):
 bundle=tmp_path/'bundle';bundle.mkdir();(bundle/'delivery-index.json').write_text(json.dumps({'tests_head':'a'*40}))
 normative=tmp_path/'norm.json';normative.write_text('{}')
 index={'tests_head':'a'*40,'skill_head':'b'*40,'run_id':'11111111-1111-4111-8111-111111111111','source_manifest':{}}
 norm={'bundle_index_sha256':'b'*64,'observations':[]}
 class Args:pass
 a=Args();a.output=tmp_path/'out';a.bundle=bundle;a.normative_report=normative;a.tests_root=c.ROOT;a.skill_root=tmp_path;a.validusage=tmp_path/'unused';a.development=False
 monkeypatch.setattr(c,'checked_dependencies',lambda *args:(h,None,{}))
 monkeypatch.setattr(c,'verify_normative',lambda *args:(index,actual_reports(),norm))
 monkeypatch.setattr(h,'source_allowlist',lambda:[]);monkeypatch.setattr(h,'raw_allowlist',lambda reports:[])
 monkeypatch.setattr(h,'verify_package',lambda *args:(_ for _ in ()).throw(ValueError('injected final verify failure')))
 assert c.build(a)==1 and not (a.output/'handoff').exists()
 staged=json.loads((a.output/'.handoff-staging/handoff-manifest.json').read_text())
 assert staged['status']=='BLOCKED'
def normative_fixture(monkeypatch,tmp_path):
 import types
 sp=importlib.util.spec_from_file_location('ds_handoff_test',ROOT/'tools/diagnostic_spec19.py');ds=importlib.util.module_from_spec(sp);sp.loader.exec_module(ds)
 vuid='VUID-VkBufferCreateInfo-size-00912';corpus=ds.index_document({'version info':{'schema version':2,'api version':'1.4.309'},'validation':{'VkBufferCreateInfo':{'core':[{'vuid':vuid,'text':'Size must be greater than 0','page':'chapters/resources.html'}]}}});corpus['source']={'sha256':'a'*64,'api_version':'1.4.309'}
 skill=tmp_path/'skill';route='references/03_api_manual/04_buffer_image_memory/buffer.md';(skill/route).parent.mkdir(parents=True);(skill/route).write_text('bounded route')
 index={'tests_head':'a'*40,'skill_head':'b'*40,'run_id':'11111111-1111-4111-8111-111111111111','chains':{'tool_capture':{'runtime_identity':{'layer_spec':(1<<22)|(4<<12)|309},'report_sha256':'c'*64}}}
 event={'chain':'tool_capture','case':'bad','phase':None,'line':1,'logfile':'tool_capture/bad.json','json_pointer':'/0/pMessageIdName','diagnostic':vuid,'log_sha256':'d'*64}
 sources={'checks19/resolve_diagnostics.py':'e'*64,'tools/diagnostic_spec19.py':'f'*64}
 spec_module=types.SimpleNamespace(load_pinned=lambda raw:corpus,lookup=ds.lookup)
 resolver=types.SimpleNamespace(verify_bundle=lambda *args:(index,{},'1'*64),verify_resolver_sources=lambda *args:sources,spec=spec_module,observations=lambda *args:[event],safe_path=lambda base,relative:base/relative)
 monkeypatch.setattr(c,'git',lambda *args:(skill/route).read_bytes())
 lookup=ds.lookup(corpus,vuid,(1<<22)|(4<<12)|309)
 observations=[{'observation':event,'lookup':lookup,'knowledge_routes':[{'path':route,'sha256':c.sha(skill/route),'skill_commit':'b'*40,'kind':'curated reading route, not source-derived normative finding'}],'chain_report_sha256':'c'*64}]
 supplied={'development':False,'status':'OBSERVED_DIAGNOSTICS_VERSION_PAIRED','resolver_sha256':'e'*64,'lookup_tool_sha256':'f'*64,'resolver_source_manifest':sources,'bundle_index_sha256':'1'*64,'bundle_run_id':index['run_id'],'tests_head':'a'*40,'skill_head':'b'*40,'source_snapshot':corpus['source'],'source_version_info':corpus['version'],'corpus_statistics':corpus['statistics'],'observations':observations,'counts':{'MATCHED_SPEC_ENTRY':1,'TOOL_DIAGNOSTIC':0,'UNKNOWN':0},'unique_observed_identifiers':[vuid]}
 validusage=tmp_path/'validusage.json';validusage.write_text('synthetic unit corpus, not runtime evidence')
 return resolver,skill,validusage,supplied
def test_real_recomputation_function_accepts_matching_unit_fixture(monkeypatch,tmp_path):
 resolver,skill,source,r=normative_fixture(monkeypatch,tmp_path)
 assert c.verify_normative(resolver,tmp_path,tmp_path,skill,source,r)[2]['counts']['MATCHED_SPEC_ENTRY']==1
@pytest.mark.parametrize('field',['observation','source','pair','counts','routes','bundle','status','development'])
def test_normative_recomputation_rejects_tampered_fields(monkeypatch,tmp_path,field):
 resolver,skill,source,original=normative_fixture(monkeypatch,tmp_path);r=copy.deepcopy(original)
 if field=='observation':r['observations'][0]['lookup']['normative_entries'][0]['text_html']='invented clause'
 elif field=='source':r['source_snapshot']['sha256']='9'*64
 elif field=='pair':r['skill_head']='9'*40
 elif field=='counts':r['counts']['MATCHED_SPEC_ENTRY']=999
 elif field=='routes':r['observations'][0]['knowledge_routes'][0]['path']='invented.md'
 elif field=='bundle':r['bundle_index_sha256']='9'*64
 elif field=='status':r['status']='PASS'
 else:r['development']=True
 with pytest.raises(ValueError,match='differs from recomputed'):c.verify_normative(resolver,tmp_path,tmp_path,skill,source,r)
def test_normative_text_is_inert_even_with_fence_payload():
 plain=h.plain_clause('<strong>must</strong> not ```<img src=x>')
 lines=h.fenced_data(plain)
 assert lines[0]=='````' and lines[-1]=='````' and '<img' not in plain
