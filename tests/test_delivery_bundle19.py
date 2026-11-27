"""Host fail-closed controls for orchestration; these do not execute Vulkan."""
import copy,importlib.util,json
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bundle',ROOT/'checks19/run_delivery_bundle.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
FILES={'transfer':'transfer-case.json','descriptor_lifetime':'descriptor-lifetime.json','pipeline_interface':'pipeline-interface.json','image_compute':'image-compute.json','tool_capture':'local-tools.json'}
def report(name):return json.loads((ROOT/'coverage/v1.0.19'/FILES[name]).read_text())
@pytest.mark.parametrize('name',FILES)
def test_recorded_schema_accepted_not_fresh_execution(name):b.verify_report(name,report(name))
@pytest.mark.parametrize('name',FILES)
@pytest.mark.parametrize('mutation',['status','case','runid','scope'])
def test_corrupt_summary_rejected(name,mutation):
 r=report(name)
 if mutation=='status':r['status']='PASS'
 elif mutation=='case':r['cases'].pop(next(iter(r['cases'])))
 elif mutation=='runid':r['run_id']='old-not-a-uuid'
 else:r['limitations']=[]
 with pytest.raises((ValueError,KeyError)):b.verify_report(name,r)
@pytest.mark.parametrize('name',FILES)
def test_fake_positive_exit_zero_rejected(name):
 r=report(name)
 if name=='transfer':r['cases']['after']['matching_words']=0
 elif name=='descriptor_lifetime':r['cases']['good']['result']['second']=0
 elif name=='pipeline_interface':r['cases']['good']['result']['output']=0
 elif name=='image_compute':r['cases']['good']['result']['pixels'][3]=0
 else:r['parsed_slices']=0
 with pytest.raises(ValueError):b.verify_report(name,r)
@pytest.mark.parametrize('operation',['delete','modify','extra','symlink'])
def test_output_tampering_rejected(tmp_path,operation):
 (tmp_path/'summary.json').write_text('{}');(tmp_path/'raw.log').write_text('real')
 snapshot=b.inventory(tmp_path)
 if operation=='delete':(tmp_path/'raw.log').unlink()
 elif operation=='modify':(tmp_path/'raw.log').write_text('fake')
 elif operation=='extra':(tmp_path/'new.log').write_text('x')
 else:(tmp_path/'link').symlink_to(tmp_path/'raw.log')
 with pytest.raises(ValueError):b.verify_snapshot(tmp_path,snapshot)
def test_missing_summary_rejected(tmp_path):
 with pytest.raises(ValueError):b.inventory(tmp_path)
def test_unbound_report_hash_rejected():
 with pytest.raises(ValueError):b.verify_hash_refs({'cases':[{'stdout_sha256':'a'*64}]},{'b'*64})
def test_bound_nested_hash_accepted():b.verify_hash_refs({'cases':[{'stdout_sha256':'a'*64}]},{'a'*64})
def test_full_commits_required(tmp_path):
 with pytest.raises(ValueError):b.verify_pair(tmp_path,tmp_path,'short','short')
def test_head_changed_rejected(monkeypatch,tmp_path):
 monkeypatch.setattr(b,'git',lambda *args:b'c'*40+b'\n')
 with pytest.raises(ValueError,match='HEAD'):b.verify_pair(tmp_path,tmp_path,'a'*40,'b'*40)
@pytest.mark.parametrize('name,key',[('descriptor_lifetime','bad'),('pipeline_interface','bad-type'),('image_compute','bad-layout')])
@pytest.mark.parametrize('change',['wrong-phase','wrong-vuid'])
def test_wrong_diagnostic_rejected(name,key,change):
 r=report(name);original=r['cases'][key]['diagnostics'][0]
 r['cases'][key]['diagnostics'][0]=original.replace('phase=','phase=WRONG-') if change=='wrong-phase' else 'NOT-TARGET'
 with pytest.raises(ValueError):b.verify_report(name,r)
def test_heuristic_off_submitted_is_not_accepted():
 r=report('image_compute');r['heuristic_off_observation']['result']['submitted']=True
 with pytest.raises(ValueError):b.verify_report('image_compute',r)
def test_log_swap_rejected_even_when_both_hashes_exist(monkeypatch,tmp_path):
 r=report('pipeline_interface');folder='cases19/pipeline_interface';sources={folder+'/run.py':r['runner_sha256'],folder+'/baseline.c':r['repair']['baseline_sha256'],folder+'/fix.patch':r['repair']['patch_sha256'],folder+'/compute.comp':r['shader']['source_sha256']}
 hashes={'compute.spv':r['shader']['spirv_sha256'],'compute.spvasm':r['shader']['disassembly_sha256'],'baseline-probe':r['repair']['baseline_binary_sha256'],'fixed-probe':r['repair']['fixed_binary_sha256']}
 def put(log,label):
  for stream in ('stdout','stderr'):hashes[label+'.'+stream]=log[stream+'_sha256']
 for k,c in r['cases'].items():put(c['log'],k)
 for field,label in [('compile','shader.compile'),('validate','shader.validate'),('disassemble','shader.dis')]:put(r['shader'][field],label)
 for field,label in [('log','patch'),('baseline_build','baseline.build'),('fixed_build','fixed.build')]:put(r['repair'][field],label)
 for k,t in r['tools'].items():put(t['log'],k+'.version')
 monkeypatch.setattr(b,'sha',lambda path:hashes[str(path.relative_to(tmp_path))])
 b.bind_report('pipeline_interface',r,sources,tmp_path)
 r['cases']['good']['log']['stdout_sha256'],r['cases']['wrong-output']['log']['stdout_sha256']=r['cases']['wrong-output']['log']['stdout_sha256'],r['cases']['good']['log']['stdout_sha256']
 with pytest.raises(ValueError,match='log binding'):b.bind_report('pipeline_interface',r,sources,tmp_path)
def test_source_mutation_between_checks_rejected(monkeypatch,tmp_path):
 root=tmp_path/'tests';skill=tmp_path/'skill';root.mkdir();skill.mkdir();(root/'coverage/v1.0.19').mkdir(parents=True);(root/'docs').mkdir();(skill/'SKILL.md').write_text('version: 1.0.19')
 (root/'docs/v1.0.19-original-plan.md').write_text('plan');(root/'runner.py').write_text('original')
 (root/'coverage/v1.0.19/pair.json').write_text(json.dumps({'skill_sha':'b'*40,'plan_sha256':b.sha(root/'docs/v1.0.19-original-plan.md'),'release_status':'BLOCKED'}))
 saved={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
 def fake_git(repo,*args):
  if args[0]=='rev-parse':return (('b' if repo==skill else 'a')*40).encode()
  if args[0]=='status':return b''
  if args[0]=='ls-files':return b'' if '--others' in args else '\0'.join(saved).encode()
  if args[0]=='show':return saved[args[1].split(':',1)[1]]
  raise AssertionError(args)
 monkeypatch.setattr(b,'git',fake_git);monkeypatch.setattr(b,'CHAINS',{'test':('runner.py','status',set())})
 b.verify_pair(root,skill,'a'*40,'b'*40)
 (root/'runner.py').write_text('changed while running')
 with pytest.raises(ValueError,match='source differs'):b.verify_pair(root,skill,'a'*40,'b'*40)
def test_existing_output_never_reused(monkeypatch,tmp_path):
 old=tmp_path/'delivery-index.json';old.write_text('{"status":"OLD_PASS"}')
 args=['bundle']
 for key in ('tools','include','loader','trace-processor','skill-root','output'):args+=['--'+key,str(tmp_path)]
 args+=['--expected-tests-head','a'*40,'--expected-skill-head','b'*40]
 monkeypatch.setattr(b.sys,'argv',args)
 with pytest.raises(FileExistsError):b.main()
 assert old.read_text()=='{"status":"OLD_PASS"}'
@pytest.mark.parametrize('case',['before','mutant'])
def test_transfer_extra_diagnostic_rejected(case):
 r=report('transfer');r['cases'][case]['message_ids'].append('NOT-TARGET');r['cases'][case]['errors']+=1
 with pytest.raises(ValueError):b.verify_report('transfer',r)
