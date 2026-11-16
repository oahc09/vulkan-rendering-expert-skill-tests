"""Host parser/pairing negative controls, not new Vulkan execution."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ds',ROOT/'tools/diagnostic_spec19.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
spec=importlib.util.spec_from_file_location('resolver',ROOT/'checks19/resolve_diagnostics.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
V='VUID-vkQueueSubmit-pCommandBuffers-00070'
def document():return {'version info':{'schema version':2,'api version':'1.4.309'},'validation':{'vkQueueSubmit':{'core':[{'vuid':V,'text':'conditional <code>data</code>','page':'chapters/cmdbuffers.html'}]}}}
def corpus():
 c=d.index_document(document());c['source']={'sha256':'a'*64};return c
def test_exact_entry_retains_inert_text_owner_condition():
 r=d.lookup(corpus(),V,(1<<22)|(4<<12)|309)
 assert r['status']=='MATCHED_SPEC_ENTRY'
 assert r['normative_entries'][0]==dict(vuid=V,text_html='conditional <code>data</code>',page='chapters/cmdbuffers.html',api_owner='vkQueueSubmit',condition_key='core')
def test_unknown_vuid_not_resolved():assert d.lookup(corpus(),'VUID-unknown-99999',(1<<22)|(4<<12)|309)['status']=='UNKNOWN'
def test_version_mismatch_is_unknown():assert d.lookup(corpus(),V,(1<<22)|(4<<12)|368)['status']=='UNKNOWN'
def test_hazard_not_normative():
 r=d.lookup(corpus(),'SYNC-HAZARD-READ-AFTER-WRITE',(1<<22)|(4<<12)|309)
 assert r['status']=='TOOL_DIAGNOSTIC' and r['normative_entry'] is None
def test_hazard_version_mismatch_unknown():assert d.lookup(corpus(),'SYNC-HAZARD-READ-AFTER-WRITE',(1<<22)|(4<<12)|368)['status']=='UNKNOWN'
def test_other_tool_identifier_unknown():assert d.lookup(corpus(),'MADE-UP-DIAGNOSTIC',(1<<22)|(4<<12)|309)['status']=='UNKNOWN'
def test_two_conditions_retained_not_overwritten():
 doc=document();doc['validation']['vkQueueSubmit']['extension X']=[dict(vuid=V,text='other condition',page='other.html')]
 c=d.index_document(doc)
 assert len(c['entries'][V])==2 and c['statistics']['unique_vuids']==1 and c['statistics']['unique_owner_condition_entries']==2
def test_two_owners_retained():
 doc=document();doc['validation']['anotherOwner']={'core':[dict(vuid=V,text='other owner',page='other.html')]}
 assert len(d.index_document(doc)['entries'][V])==2
def test_same_coordinate_conflict_rejected():
 doc=document();doc['validation']['vkQueueSubmit']['core'].append(dict(vuid=V,text='conflicting',page='other.html'))
 with pytest.raises(ValueError,match='conflicting'):d.index_document(doc)
def test_identical_duplicate_counted():
 doc=document();doc['validation']['vkQueueSubmit']['core']*=2
 c=d.index_document(doc);assert c['statistics']['identical_duplicates']==1 and len(c['entries'][V])==1
def test_double_colon_official_id_preserved():
 doc=document();doc['validation']['vkQueueSubmit']['core'][0]['vuid']='VUID-vkAllocateDescriptorSets-pAllocateInfo::descriptorSetCount-arraylength'
 assert d.index_document(doc)['statistics']['unique_vuids']==1
@pytest.mark.parametrize('field,value',[('validation',{}),('version info',{'schema version':1,'api version':'1.4.309'})])
def test_invalid_schema_rejected(field,value):
 doc=document();doc[field]=value
 with pytest.raises(ValueError):d.index_document(doc)
def test_wrong_source_hash_rejected():
 with pytest.raises(ValueError,match='digest'):d.load_pinned(json.dumps(document()).encode())
def test_duplicate_json_keys_rejected():
 with pytest.raises(ValueError):d.parse_json('{"x":1,"x":2}')
@pytest.mark.parametrize('v',[True,-1,2**32,'1.4.309'])
def test_malformed_api_version_rejected(v):
 with pytest.raises(ValueError):d.api_version(v)
@pytest.mark.parametrize('path',['../outside','/absolute','a/../../outside'])
def test_path_escape_rejected(tmp_path,path):
 with pytest.raises(ValueError):cli.safe_path(tmp_path,path)
def test_symlink_evidence_rejected(tmp_path):
 (tmp_path/'real').write_text('x');(tmp_path/'link').symlink_to(tmp_path/'real')
 with pytest.raises(ValueError):cli.safe_path(tmp_path,'link')
def test_summary_invented_vuid_rejected(tmp_path):
 folder=tmp_path/'transfer';folder.mkdir();(folder/'before.json').write_text('[{"pMessageIdName":"REAL"}]')
 with pytest.raises(ValueError):cli.observations(tmp_path,{'transfer':{'cases':{'before':{'message_ids':['INVENTED']}}}})
def test_phase_line_retained_from_raw_log(tmp_path):
 folder=tmp_path/'pipeline_interface';folder.mkdir();text='IDENTITY {}\nVUID phase=pipeline-create id='+V+'\n';(folder/'bad.stderr').write_text(text)
 r=cli.observations(tmp_path,{'pipeline_interface':{'cases':{'bad':{'diagnostics':[text.splitlines()[1]]}}}})
 assert r[0]['line']==2 and r[0]['phase']=='pipeline-create' and r[0]['log_sha256']==hashlib.sha256(text.encode()).hexdigest()
def test_fake_summary_phase_rejected(tmp_path):
 folder=tmp_path/'pipeline_interface';folder.mkdir();(folder/'bad.stderr').write_text('VUID phase=real id='+V+'\n')
 with pytest.raises(ValueError):cli.observations(tmp_path,{'pipeline_interface':{'cases':{'bad':{'diagnostics':['VUID phase=fake id='+V]}}}})
def test_development_bundle_rejected(tmp_path):
 (tmp_path/'delivery-index.json').write_text(json.dumps({'development':True,'status':'PASS_FIVE_BOUNDED_LOCAL_CHAINS','entrypoint_in_declared_head':True}))
 with pytest.raises(ValueError,match='strict'):cli.verify_bundle(tmp_path,tmp_path,tmp_path)
@pytest.mark.parametrize('variant',[1,2,7])
def test_nonzero_api_variant_rejected(variant):
 with pytest.raises(ValueError):d.api_version((variant<<29)|(1<<22)|(4<<12)|309)
def test_wrong_checkout_resolver_rejected(tmp_path):
 with pytest.raises(ValueError,match='selected tests checkout'):cli.verify_resolver_sources(tmp_path,'a'*40,development=True)
def test_uncommitted_resolver_rejected(monkeypatch):
 monkeypatch.setattr(cli.subprocess,'check_output',lambda *args,**kw:b'wrong committed code')
 with pytest.raises(ValueError,match='not at bundle commit'):cli.verify_resolver_sources(cli.ROOT,'a'*40)
def test_development_source_hashes_explicit():
 r=cli.verify_resolver_sources(cli.ROOT,'a'*40,development=True)
 assert set(r)=={'checks19/resolve_diagnostics.py','tools/diagnostic_spec19.py'}
def controlled_index():
 return {'entrypoint_sha256':'e'*64,'supervisor_sha256':'a'*64,'execution_source_manifest':{'checks19/run_delivery_bundle.py':'e'*64,'checks19/process_supervisor19.py':'a'*64},'source_manifest':{'checks19/process_supervisor19.py':'a'*64},'steps':[{'pid':123,'pgid':123,'returncode':0,'timed_out':False,'cancelled':False,'budget_exhausted':False,'unexpected_descendants':False,'group_cleanup':{'pgid':123,'group_gone':True,'term_sent':True,'kill_sent':True,'reaped_descendants':[]}}]}
def test_complete_process_control_accepted():cli.verify_process_control(controlled_index())
@pytest.mark.parametrize('field',['supervisor_sha256','execution_source_manifest','source_manifest','steps'])
def test_deleted_control_index_field_rejected(field):
 d=controlled_index();del d[field]
 with pytest.raises(ValueError):cli.verify_process_control(d)
@pytest.mark.parametrize('field',['group_cleanup','cancelled','timed_out','budget_exhausted','unexpected_descendants','pid','pgid','returncode'])
def test_deleted_step_control_field_rejected(field):
 d=controlled_index();del d['steps'][0][field]
 with pytest.raises(ValueError):cli.verify_process_control(d)
@pytest.mark.parametrize('field',['pgid','group_gone','term_sent','kill_sent','reaped_descendants'])
def test_deleted_cleanup_field_rejected(field):
 d=controlled_index();del d['steps'][0]['group_cleanup'][field]
 with pytest.raises(ValueError):cli.verify_process_control(d)
@pytest.mark.parametrize('field',['cancelled','timed_out','budget_exhausted','unexpected_descendants'])
def test_true_failure_flag_rejected(field):
 d=controlled_index();d['steps'][0][field]=True
 with pytest.raises(ValueError):cli.verify_process_control(d)
def test_wrong_helper_source_digest_rejected():
 d=controlled_index();d['source_manifest']['checks19/process_supervisor19.py']='b'*64
 with pytest.raises(ValueError):cli.verify_process_control(d)
def test_unreaped_descendant_rejected():
 d=controlled_index();d['steps'][0]['group_cleanup']['reaped_descendants']=[456]
 with pytest.raises(ValueError):cli.verify_process_control(d)
