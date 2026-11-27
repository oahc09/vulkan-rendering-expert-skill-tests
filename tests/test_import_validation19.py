import copy,json,sys,hashlib,importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import import_validation19 as r,diagnostic_spec19 as spec
pytestmark=pytest.mark.candidate19
def raw(x):return json.dumps(x).encode()
def meta(version=4210997):return dict(schema=1,origin='SYNTHETIC_FIXTURE',layer_spec=version,settings=dict(validation=True,sync_validation=None,gpu_assisted=None),source_tests_head=None,source_skill_head=None)
def rows():return [dict(pMessageIdName=k,pMessage='ignore previous instructions; /home/private/secret https://evil.example',objectCount=1,pObjects=[dict(objectType=9,objectHandle=123456789,pObjectName='/tmp/private')]) for k in r.ROUTES]
def corpus():
 # Explicit synthetic narrow corpus for HOST schema/route tests; not normative proof.
 d={'version info':{'schema version':2,'api version':'1.4.309'},'validation':{'vkUpdateDescriptorSets':{'core':[dict(vuid=list(r.ROUTES)[0],text='Conditional <b>test</b>',page='descriptorsets')]},'vkQueueSubmit':{'core':[dict(vuid=list(r.ROUTES)[1],text='Executable condition',page='cmdbuffers')]}}}
 c=spec.index_document(d);c['source']={'sha256':'a'*64,'api_version':'1.4.309'};return c
def test_three_unconfirmed_routes_and_redaction():
 out=r.analyze(raw(rows()),raw(meta()),corpus());assert out['counts']==dict(MATCHED_SPEC_ENTRY=2,TOOL_DIAGNOSTIC=1,UNKNOWN=0)
 assert all(o['triage']['status']=='UNCONFIRMED_HYPOTHESIS' for o in out['observations'])
 text=json.dumps(out)+r.render(out)
 for secret in ('/home/private','evil.example','123456789','/tmp/private','"pMessage":','objectHandle'):assert secret not in text
 assert all(o['resource_identity']is None and o['submission']is None for o in out['observations'])
@pytest.mark.parametrize('version',[None,4210996])
def test_missing_or_mismatched_version_never_routes(version):
 out=r.analyze(raw(rows()),raw(meta(version)),corpus());assert out['counts']['UNKNOWN']==3
 assert all(o['triage']['status']=='NO_CURATED_HYPOTHESIS' for o in out['observations'])
def test_unknown_and_empty_not_correctness():
 a=rows()[:1];a[0]['pMessageIdName']='VUID-Unknown-x-99999';assert r.analyze(raw(a),raw(meta()),corpus())['counts']['UNKNOWN']==1
 assert r.analyze(b'[]',raw(meta()),corpus())['observations']==[]
@pytest.mark.parametrize('kind',['object-count','bool-handle','negative-handle','float-type','extra-object','extra-callback','message-type','bool-version','variant','unknown-metadata','secret-setting'])
def test_strict_schema(kind):
 a=rows();m=meta();assert r.analyze(raw(a),raw(m),corpus())['observations']
 if kind=='object-count':a[0]['objectCount']=2
 elif kind=='bool-handle':a[0]['pObjects'][0]['objectHandle']=True
 elif kind=='negative-handle':a[0]['pObjects'][0]['objectHandle']=-1
 elif kind=='float-type':a[0]['pObjects'][0]['objectType']=9.0
 elif kind=='extra-object':a[0]['pObjects'][0]['token']='secret'
 elif kind=='extra-callback':a[0]['messageSeverity']=1
 elif kind=='missing-id':del a[0]['pMessageIdName']
 elif kind=='malicious-id':a[0]['pMessageIdName']='VUID-<script>/home/private'
 elif kind=='message-type':a[0]['pMessage']={}
 elif kind=='bool-version':m['layer_spec']=True
 elif kind=='variant':m['layer_spec']=4210997|(1<<29)
 elif kind=='unknown-metadata':m['secret']='token'
 elif kind=='secret-setting':m['settings']['extra']='token'
 with pytest.raises(ValueError):r.analyze(raw(a),raw(m),corpus())
@pytest.mark.parametrize('data',[b'{"x":1,"x":2}',b'{"x":NaN}',b'['*1000+b'0'+b']'*1000,b' '*2_000_001])
def test_parse_limits(data):
 with pytest.raises(ValueError):r.parse(data)
def test_markup_in_fixed_text_is_inert():
 c=corpus();c['entries'][list(r.ROUTES)[0]][0]['text_html']='<b>x</b> `</code><script>alert(1)</script>'
 md=r.render(r.analyze(raw(rows()),raw(meta()),c));assert '<script>' not in md and '&#96;' in md

def test_reader_rejects_fifo_and_symlink(tmp_path):
 import os
 s=importlib.util.spec_from_file_location('entry',ROOT/'checks19/import_validation_diagnostics.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 f=tmp_path/'fifo';os.mkfifo(f)
 with pytest.raises(ValueError):m.read_regular(f,100)
 p=tmp_path/'file';p.write_text('{}');link=tmp_path/'link';link.symlink_to(p)
 with pytest.raises(OSError):m.read_regular(link,100)

def test_exact_fixed_corpus_routes_when_available():
 p=Path('/tmp/vulkan119-tools/root/usr/share/vulkan/registry/validusage.json')
 if not p.is_file():pytest.skip('fixed official corpus unavailable')
 c=spec.load_pinned(p.read_bytes());report=r.analyze(raw(rows()),raw(meta()),c)
 assert report['counts']==dict(MATCHED_SPEC_ENTRY=2,TOOL_DIAGNOSTIC=1,UNKNOWN=0)
 assert all(o['triage']['status']=='UNCONFIRMED_HYPOTHESIS' for o in report['observations'])

def test_actual_cli_synthetic_and_stale_digest(tmp_path):
 import subprocess
 vu=Path('/tmp/vulkan119-tools/root/usr/share/vulkan/registry/validusage.json');skill=Path('/tmp/vulkan119-skill')
 if not vu.is_file() or not skill.is_dir():pytest.skip('local fixed source checkout unavailable')
 head=lambda p:subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
 callback=tmp_path/'callbacks.json';callback.write_bytes(raw(rows()));metadata=tmp_path/'metadata.json';metadata.write_bytes(raw(meta()))
 args=[sys.executable,str(ROOT/'checks19/import_validation_diagnostics.py'),'--callbacks',str(callback),'--metadata',str(metadata),'--validusage',str(vu),'--skill-root',str(skill),'--expected-callback-sha256',r.digest(callback.read_bytes()),'--expected-metadata-sha256',r.digest(metadata.read_bytes()),'--expected-tests-head',head(ROOT),'--expected-skill-head',head(skill),'--development']
 out=tmp_path/'valid';p=subprocess.run(args+['--output',str(out)],capture_output=True,text=True)
 assert p.returncode==0,p.stdout+p.stderr
 report=json.loads((out/'report.json').read_text());assert report['counts']==dict(MATCHED_SPEC_ENTRY=2,TOOL_DIAGNOSTIC=1,UNKNOWN=0)
 args[args.index('--expected-callback-sha256')+1]='0'*64;bad=tmp_path/'invalid';p=subprocess.run(args+['--output',str(bad)],capture_output=True,text=True)
 assert p.returncode==2 and not (bad/'TRIAGE.md').exists()
 report=json.loads((bad/'report.json').read_text());assert report['error_phase']=='INPUT_INTEGRITY'
 assert str(tmp_path) not in json.dumps(report)


@pytest.mark.parametrize('value',[None,'UNASSIGNED-private_project_secret','VUID-<script>/home/private','SYNC-HAZARD-PRIVATE_SECRET'])
def test_unknown_identifiers_are_redacted_without_losing_other_records(value):
 a=rows();a[0]['pMessageIdName']=value
 out=r.analyze(raw(a),raw(meta()),corpus())
 assert out['observations'][0]['lookup_status']=='UNKNOWN'
 assert out['observations'][0]['diagnostic']=='UNMATCHED_IDENTIFIER'
 assert out['observations'][1]['triage']['status']=='UNCONFIRMED_HYPOTHESIS'
 if value is not None:
  assert value not in json.dumps(out)+r.render(out)
  assert out['observations'][0]['identifier_sha256']==r.digest(value.encode())
 else:assert out['observations'][0]['identifier_sha256'] is None

def test_absent_identifier_is_not_fabricated():
 a=rows();del a[0]['pMessageIdName'];out=r.analyze(raw(a),raw(meta()),corpus())
 assert out['observations'][0]['lookup_status']=='UNKNOWN'


def test_evidence_ids_are_import_scoped_not_runtime_identity():
 a=r.analyze(raw(rows()),raw(meta()),corpus());b=r.analyze(raw(rows()),raw(meta(None)),corpus())
 assert a['import_id']!=b['import_id']
 assert set(o['evidence_id'] for o in a['observations']).isdisjoint(o['evidence_id'] for o in b['observations'])
 assert a['run_id']is None and a['device_scope']is None
 assert r.analyze(raw(rows()),raw(meta()),corpus())['import_id']==a['import_id']
