from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import shader_target19 as s
pytestmark=pytest.mark.host_unit
H='a'*64
ID=dict(run='r',device='d',generation=1)
FACT=dict(ID,shaderFloat64=True)
BASE=dict(artifact_sha256=H,capabilities=['Shader','Float64'],extensions=[],extraction=dict(artifact_sha256=H,exit_code=0,capabilities=['Shader','Float64'],extensions=[]),validation=dict(artifact_sha256=H,target_env='vulkan1.1',exit_code=0),identity=ID,support=FACT,enabled=FACT)
def check(**kw):
 args=BASE|kw
 if 'extraction' not in kw:args['extraction']=BASE['extraction']|{'capabilities':args['capabilities'],'extensions':args['extensions']}
 return s.admit(**args)
def test_feature_admission_not_execution():
 r=check();assert r['status']=='WITHIN_CHECKED_CAPABILITY_SLICE' and 'actual shader execution and output' in r['remaining']
def test_shader_without_optional_feature():assert check(capabilities=['Shader'],support=None,enabled=None)['status']=='WITHIN_CHECKED_CAPABILITY_SLICE'
@pytest.mark.parametrize('field,status',[('support','REJECTED_UNSUPPORTED_FLOAT64'),('enabled','REJECTED_FLOAT64_NOT_ENABLED')])
def test_validation_success_is_not_device_admission(field,status):assert check(**{field:FACT|{'shaderFloat64':False}})['status']==status
@pytest.mark.parametrize('field',['support','enabled'])
def test_unknown_feature(field):assert check(**{field:ID})['status']=='UNKNOWN'
@pytest.mark.parametrize('field,value',[('device','other'),('generation',2),('generation',True),('run','old')])
def test_stale_creation_record(field,value):assert check(enabled=FACT|{field:value})['status']=='UNKNOWN'
def test_validator_target_rejected():assert check(validation=BASE['validation']|{'exit_code':1})['status']=='REJECTED_TARGET_VALIDATION'
def test_wrong_binary():assert check(validation=BASE['validation']|{'artifact_sha256':'b'*64})['status']=='UNKNOWN'
def test_unknown_capability():assert check(capabilities=['Shader','Int64'])['status']=='UNKNOWN'
def test_unknown_extension():assert check(extensions=['SPV_KHR_unknown'])['status']=='UNKNOWN'
def test_shader_required():assert check(capabilities=['Float64'])['status']=='REJECTED_MISSING_SHADER_CAPABILITY'
@pytest.mark.parametrize('change',[{'capabilities':['Shader','Shader']},{'capabilities':[]},{'artifact_sha256':'bad'},{'validation':BASE['validation']|{'exit_code':True}},{'identity':ID|{'generation':True}},{'support':FACT|{'shaderFloat64':1}}])
def test_malformed(change):
 with pytest.raises(ValueError):check(**change)

def test_cannot_omit_float64_from_extracted_binary():
 assert check(capabilities=['Shader'],extraction=BASE['extraction'],support=None,enabled=None)['status']=='UNKNOWN'
@pytest.mark.parametrize('extraction',[None,BASE['extraction']|{'artifact_sha256':'b'*64},BASE['extraction']|{'exit_code':1},BASE['extraction']|{'exit_code':False}])
def test_extraction_must_be_paired_and_successful(extraction):assert check(extraction=extraction)['status']=='UNKNOWN'

def actual():
 import json,hashlib
 root=Path(__file__).parents[1];d=json.loads((root/'coverage/v1.0.19/shader-target.json').read_text())
 assert hashlib.sha256((root/'cases19/shader_target/run.py').read_bytes()).hexdigest()==d['runner_sha256']
 for c in d['cases'].values():assert hashlib.sha256((root/'cases19/shader_target'/c['source']).read_bytes()).hexdigest()==c['source_sha256']
 return d['cases']
def test_real_float64_tool_pass_still_needs_device_evidence():
 c=actual()['float64_11']
 r=s.admit(artifact_sha256=c['spirv_sha256'],capabilities=c['capabilities'],extensions=c['extensions'],extraction=c['extraction'],validation=c['validate'],identity=ID,support=None,enabled=None)
 assert r['status']=='UNKNOWN'
def test_real_wrong_target_same_binary_rejected():
 c=actual()['base12'];v=c['wrong_target']
 assert v['artifact_sha256']==c['spirv_sha256'] and v['exit_code']!=0
 r=s.admit(artifact_sha256=c['spirv_sha256'],capabilities=c['capabilities'],extensions=c['extensions'],extraction=c['extraction'],validation=v,identity=ID,support=None,enabled=None)
 assert r['status']=='REJECTED_TARGET_VALIDATION'
