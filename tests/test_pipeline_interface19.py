"""CPU parser/contract controls; actual complete API evidence is tested separately."""
from pathlib import Path
import sys,hashlib
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import pipeline_interface19 as p
pytestmark=pytest.mark.host_unit
H='a'*64
ASM='''OpCapability Shader
OpEntryPoint GLCompute %main "main"
OpDecorate %Block Block
OpDecorate %out DescriptorSet 0
OpDecorate %out Binding 0
%Block = OpTypeStruct %uint
%ptr = OpTypePointer StorageBuffer %Block
%out = OpVariable %ptr StorageBuffer
'''
def reflect(text=ASM,**kw):
 h=hashlib.sha256(text.encode()).hexdigest()
 return p.reflect(**(dict(artifact_sha256=H,disassembly=text,extraction_sha256=h,validation=dict(artifact_sha256=H,disassembly_sha256=h,exit_code=0,target_env='vulkan1.1'))|kw))
LAY=[dict(set=0,binding=0,type='storage-buffer',count=1,stages=['compute'])]
def test_bound_reflection_and_layout():
 r=reflect();assert r['entrypoint']=='main';assert p.compare(r,LAY,artifact_sha256=H)['status']=='WITHIN_CHECKED_INTERFACE'
@pytest.mark.parametrize('text',[ASM.replace('Shader','Float64'),ASM+'OpExtension "other"\n',ASM+'OpEntryPoint GLCompute %other "two"\n',ASM.replace('StorageBuffer','Uniform'),ASM.replace('StorageBuffer','PushConstant'),ASM.replace('OpTypeStruct','OpTypeArray'),ASM.replace('OpDecorate %Block Block',''),ASM.replace('OpDecorate %out Binding 0',''),ASM+'OpDecorate %out Binding 0\n'])
def test_unreviewed_or_incomplete_shape_unknown(text):assert reflect(text)['status']=='UNKNOWN'
def test_wrong_tool_pair():
 assert reflect(extraction_sha256='0'*64)['status']=='UNKNOWN'
 assert reflect(validation={'artifact_sha256':'b'*64})['status']=='UNKNOWN'
@pytest.mark.parametrize('layout,vuid',[([], '07988'),([LAY[0]|{'type':'uniform-buffer'}],'07990'),([LAY[0]|{'stages':['vertex']}],'07988'),([LAY[0]|{'count':0}],'07988')])
def test_interface_negatives(layout,vuid):assert p.compare(reflect(),layout,artifact_sha256=H)['vuids'][0].endswith(vuid)
def test_wrong_shader_not_admitted():assert p.compare(reflect(),LAY,artifact_sha256='b'*64)['status']=='UNKNOWN'
@pytest.mark.parametrize('layout',[[LAY[0],LAY[0]],[LAY[0]|{'set':True}],[LAY[0]|{'count':-1}],[LAY[0]|{'stages':'compute'}]])
def test_malformed_layout(layout):
 with pytest.raises(ValueError):p.compare(reflect(),layout,artifact_sha256=H)

@pytest.mark.parametrize('typ',['storage-buffer-dynamic','mutable','unknown'])
def test_other_layout_semantics_not_false_type_vuid(typ):assert p.compare(reflect(),[LAY[0]|{'type':typ}],artifact_sha256=H)['status']=='UNKNOWN'
@pytest.mark.parametrize('resources',[[],None,[{}],[dict(set=True,binding=0,type='storage-buffer',count=1,stage='compute')]])
def test_incomplete_reflection_cannot_pass(resources):assert p.compare(reflect()|{'descriptors':resources},LAY,artifact_sha256=H)['status']=='UNKNOWN'

def test_actual_repair_rule_and_api_pair():
 import json
 root=Path(__file__).parents[1];case=root/'cases19/pipeline_interface'
 d=json.loads((root/'coverage/v1.0.19/pipeline-interface.json').read_text())
 for file,expected in [(root/'tools/pipeline_interface19.py',d['rule_sha256']),(case/'run.py',d['runner_sha256']),(case/'baseline.c',d['repair']['baseline_sha256']),(case/'fix.patch',d['repair']['patch_sha256']),(case/'compute.comp',d['shader']['source_sha256'])]:assert hashlib.sha256(file.read_bytes()).hexdigest()==expected
 h=d['shader']['spirv_sha256']
 for mode,c in d['cases'].items():
  assert c['shader_sha256']==h
  assert p.compare(d['reflection'],c['layout'],artifact_sha256=h)==c['admission']
  assert c['admission']['vuids']==[x.split(' id=')[1] for x in c['diagnostics']]
 assert d['cases']['good']['result']['output']==42
 assert d['cases']['wrong-output']['result']['output']==42 and d['cases']['wrong-output']['result']['exit_code']==6
 assert d['cases']['bad-type']['result']['pipeline_result']==-1000011001
 assert d['cases']['missing-binding']['layout'][0]['binding']==1
