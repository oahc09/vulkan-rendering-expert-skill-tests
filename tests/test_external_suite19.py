import copy,json
import pytest
from checks19 import run_external_suite as e
from tools import external_suite19 as v
RUN_ID="11111111-1111-4111-8111-111111111111"

def baseline():
 labels=e.TASKS;classes=['ORIGINAL_CLASS_HOST_TEST_DOUBLE','ORIGINAL_ENGINE_SOFTWARE_VULKAN_BUG','ORIGINAL_NEIGHBOR_REGRESSIONS_NOT_NEW_BUGS']
 return {'planned_counts':dict(e.PLANNED),'pending':[],'steps':[{'label':x,'returncode':0,'pid':100+i,'timed_out':False,'cancelled':False,'budget_exhausted':False,'unexpected_descendants':False,'group_cleanup':{'pgid':100+i,'group_gone':True,'term_sent':True,'kill_sent':True,'reaped_descendants':[]}} for i,x in enumerate(labels)],'verified':[{'task':x,'child_run_id':str(i),'classification':classes[i],'original_bugs':1 if i<2 else 0,'gpu_executed':i>0} for i,x in enumerate(labels)]}
def test_complete():e.complete(baseline())
@pytest.mark.parametrize('key',['timed_out','cancelled','budget_exhausted','unexpected_descendants'])
def test_process_fault(key):
 d=baseline();d['steps'][0][key]=True
 with pytest.raises(ValueError):e.complete(d)
def test_pending():
 d=baseline();d['pending']=['related_gpu']
 with pytest.raises(ValueError):e.complete(d)
def test_classification():
 d=baseline();d['verified'][2]['original_bugs']=3
 with pytest.raises(ValueError):e.complete(d)
def test_host_not_gpu():
 d=baseline();d['verified'][0]['gpu_executed']=True
 with pytest.raises(ValueError):e.complete(d)
def test_child_id_reuse():
 d=baseline();d['verified'][1]['child_run_id']='0'
 with pytest.raises(ValueError):e.complete(d)
def test_clean_fields_required():
 d=baseline();del d['steps'][0]['group_cleanup']['kill_sent']
 with pytest.raises(KeyError):e.complete(d)
def test_bool_exit():
 d=baseline();d['steps'][0]['returncode']=False
 with pytest.raises(ValueError):e.complete(d)
def test_pid_mismatch():
 d=baseline();d['steps'][0]['group_cleanup']['pgid']=999
 with pytest.raises(ValueError):e.complete(d)
def test_fake_pass_report(tmp_path):
 (tmp_path/'report.json').write_text(json.dumps({'status':'PASS','artifacts':{},'run_id':RUN_ID,'output_root':str(tmp_path)}))
 with pytest.raises(ValueError):v.verify_fence(tmp_path,{},RUN_ID)
def test_inventory_tamper(tmp_path):
 (tmp_path/'x').write_text('new');(tmp_path/'report.json').write_text(json.dumps({'artifacts':{'x':'0'*64}}))
 with pytest.raises(ValueError):v.read_report(tmp_path)
def test_inventory_symlink(tmp_path):
 (tmp_path/'secret').symlink_to('/etc/passwd')
 with pytest.raises(ValueError):v.inventory(tmp_path)
def test_nested_same_index_is_not_excluded(tmp_path):
 (tmp_path/'sub').mkdir();(tmp_path/'sub/external-index.json').write_text('real')
 assert 'sub/external-index.json' in e.inventory(tmp_path)
def test_config_unknown_key(tmp_path):
 p=tmp_path/'x';p.write_text(json.dumps({'command':'anything'}))
 with pytest.raises(ValueError):e.config(p)
def test_duplicate_key():
 with pytest.raises(ValueError):json.loads('{"x":1,"x":2}',object_pairs_hook=e.unique)
@pytest.fixture
def related_fixture(tmp_path,monkeypatch):
 base=tmp_path/'assets';root=tmp_path/'child';root.mkdir();cfg={'artifact_root':str(base),'_expected_tests_head':'1'*40,'_expected_skill_head':'2'*40,'_expected_pair_sha256':'3'*64}
 monkeypatch.setattr(v.r,'verify_inputs',lambda path:{'test_fixture_only':True})
 monkeypatch.setattr(v.a,'verify_artifacts',lambda path:{'environment':{'VK_DRIVER_FILES':'fixture'}})
 for variant in ('before','after'):
  p=base/f'amber951-{variant}-build/amber/amber';p.parent.mkdir(parents=True);p.write_text('mock binary')
 d={'environment':{'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','VK_DRIVER_FILES':'fixture'},'provenance':{'tests':{'head':'1'*40,'porcelain':[]},'skill':{'head':'2'*40,'porcelain':[]},'pair_sha256':'3'*64,'pair':json.loads((v.a.ROOT/'coverage/v1.0.19/pair.json').read_text())},'run_id':RUN_ID,'output_root':str(root.resolve()),'status':'RELATED_ORIGINAL_REGRESSIONS_PASSED','manifest_sha256':v.a.MANIFEST,'source_commits':{'before':v.a.BEFORE,'after':v.a.AFTER},'implementation_sha256':{x:v.a.fh(v.a.ROOT/x) for x in v.r.OWN},'steps':[]}
 for i,(case,variant) in enumerate(v.r.ORDER):
  cmd=v.r.argv(base,case,variant);stdout=v.r.CASES[case][1];stderr=v.r.WARN if case.startswith('draw_') else ''
  (root/f'{i}.stdout').write_text(stdout);(root/f'{i}.stderr').write_text(stderr)
  d['steps'].append({'case':case,'variant':variant,'argv':cmd,'timed_out':False,'returncode':0,'source_sha256':v.r.CASES[case][0],'binary_sha256':v.a.fh(cmd[0]),'stdout_sha256':v.a.fh(root/f'{i}.stdout'),'stderr_sha256':v.a.fh(root/f'{i}.stderr')})
 d['artifacts']=v.inventory(root);(root/'report.json').write_text(json.dumps(d))
 assert v.verify_related(root,cfg,RUN_ID)['regression_executions']==6
 return root,cfg,d

def resign(root,d):
 for i,s in enumerate(d['steps']):
  for stream in ('stdout','stderr'):s[stream+'_sha256']=v.a.fh(root/f'{i}.{stream}')
 d['artifacts']=v.inventory(root);(root/'report.json').write_text(json.dumps(d))

def test_complete_related_fixture(related_fixture):
 root,cfg,d=related_fixture;assert v.verify_related(root,cfg,RUN_ID)['original_bugs']==0

def test_coordinated_pass_claim_without_oracle(related_fixture):
 root,cfg,d=related_fixture;(root/'0.stdout').write_text('Summary: 1 pass, 0 fail\n');resign(root,d)
 with pytest.raises(ValueError,match='oracle transcript'):v.verify_related(root,cfg,RUN_ID)

def test_coordinated_extra_diagnostic(related_fixture):
 root,cfg,d=related_fixture;(root/'0.stderr').write_text('surprise failure');resign(root,d)
 with pytest.raises(ValueError,match='diagnostics'):v.verify_related(root,cfg,RUN_ID)

def test_coordinated_case_missing(related_fixture):
 root,cfg,d=related_fixture;d['steps'].pop();resign(root,d)
 with pytest.raises(ValueError,match='step order'):v.verify_related(root,cfg,RUN_ID)

def test_coordinated_source_claim(related_fixture):
 root,cfg,d=related_fixture;d['steps'][0]['source_sha256']='0'*64;resign(root,d)
 with pytest.raises(ValueError,match='source/invocation'):v.verify_related(root,cfg,RUN_ID)

def test_coordinated_arbitrary_command(related_fixture):
 root,cfg,d=related_fixture;d['steps'][0]['argv']=['unapproved'];resign(root,d)
 with pytest.raises(ValueError,match='source/invocation'):v.verify_related(root,cfg,RUN_ID)
def test_copied_old_report_to_fresh_directory(related_fixture,tmp_path):
 import shutil
 root,cfg,d=related_fixture;fresh=tmp_path/'copied';shutil.copytree(root,fresh)
 with pytest.raises(ValueError,match='report identity'):v.verify_related(fresh,cfg,RUN_ID)
def test_old_report_wrong_run_uuid(related_fixture):
 root,cfg,d=related_fixture
 with pytest.raises(ValueError,match='report identity'):v.verify_related(root,cfg,'22222222-2222-4222-8222-222222222222')
def test_task_swap_fails(related_fixture):
 root,cfg,d=related_fixture
 with pytest.raises((ValueError,KeyError)):v.verify('amber_gpu',root,cfg,RUN_ID)
def test_coordinated_extra_artifact(related_fixture):
 root,cfg,d=related_fixture;(root/'invented-proof').write_text('extra');resign(root,d)
 with pytest.raises(ValueError,match='unexpected artifacts'):v.verify_related(root,cfg,RUN_ID)
def test_environment_claim_changed(related_fixture):
 root,cfg,d=related_fixture;d['environment']['LD_PRELOAD']='other.so';resign(root,d)
 with pytest.raises(ValueError,match='environment'):v.verify_related(root,cfg,RUN_ID)
def test_head_claim_changed(related_fixture):
 root,cfg,d=related_fixture;d['provenance']['tests']['head']='4'*40;resign(root,d)
 with pytest.raises(ValueError,match='provenance'):v.verify_related(root,cfg,RUN_ID)
def test_dirty_claim(related_fixture):
 root,cfg,d=related_fixture;d['provenance']['skill']['porcelain']=[' M SKILL.md'];resign(root,d)
 with pytest.raises(ValueError,match='provenance'):v.verify_related(root,cfg,RUN_ID)
def test_pair_claim_changed(related_fixture):
 root,cfg,d=related_fixture;d['provenance']['pair_sha256']='0'*64;resign(root,d)
 with pytest.raises(ValueError,match='pair'):v.verify_related(root,cfg,RUN_ID)
