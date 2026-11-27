"""Host tamper checks; committed actual cohort facts reconstructed as fixture logs.
These tests do not claim to rerun Vulkan. Every mutation starts from a passing gate.
"""
import copy,importlib.util,json,pathlib,uuid
import pytest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v=module('resource_verifier_test',ROOT/'checks19/resource_suite19.py')
e=module('resource_entry_test',ROOT/'checks19/run_resource_suite.py')
NAMES={'device_address':'device-address','ray_query':'ray-query','robust_buffer':'robust-buffer','headless_wsi':'headless-wsi'}
PREFIX={'device_address':'address-query ','ray_query':'as-create ','robust_buffer':'descriptor-update ','headless_wsi':'invalid-acquire '}
def fixture(tmp,family):
 d=json.loads((ROOT/'coverage/v1.0.19'/(NAMES[family]+'.json')).read_text());layer=tmp/'layers';layer.mkdir();(layer/'VkLayer_khronos_validation.json').write_text(json.dumps({'layer':{'api_version':'1.4.309','implementation_version':1}}));t={'layer_path':str(layer)}
 if family=='device_address':(tmp/'inventory.stdout').write_text(json.dumps(d['capability_inventory']['capabilities']))
 rewrite(tmp,family,d);getattr(v,'verify_'+family)(tmp,t,d);return d,t

def rewrite(tmp,family,d):
 for name,c in d['cases'].items():
  (tmp/(name+'.stdout')).write_text('\n'.join(json.dumps(x) for x in c['records'])+'\n');(tmp/(name+'.stderr')).write_text(''.join(PREFIX[family]+x+'\n' for x in c['diagnostics']))
  for stream in ('stdout','stderr'):c[stream+'_sha256']=v.sha(tmp/(name+'.'+stream))

@pytest.mark.parametrize('family',list(NAMES))
def test_complete_positive(tmp_path,family):fixture(tmp_path,family)
@pytest.mark.parametrize('family',list(NAMES))
@pytest.mark.parametrize('mutation',['pixel','extra-diagnostic','submitted-negative','duplicate','wrong-exit','wrong-phase'])
def test_coordinated_mutations(tmp_path,family,mutation):
 d,t=fixture(tmp_path,family);c=d['cases']['good'];negative=next(k for k in d['cases'] if k not in ('good','wrong-output'))
 if mutation=='pixel':
  rows=c['records'];row=next(x for x in rows if x['kind']==('frame' if family=='headless_wsi' else 'readback'));key='pixels' if family=='headless_wsi' else 'output' if family=='robust_buffer' else 'values';row[key][0]^=1
 elif mutation=='extra-diagnostic':c['diagnostics'].append('VUID-UNEXPECTED-99999')
 elif mutation=='submitted-negative':
  row=d['cases'][negative]['records'][-1];row['frames']=1 if family=='headless_wsi' else row.get('frames',0);row['submitted']=True
 elif mutation=='duplicate':c['records'].insert(0,copy.deepcopy(c['records'][0]))
 elif mutation=='wrong-exit':c['exit_code']=6
 rewrite(tmp_path,family,d)
 if mutation=='wrong-phase':
  path=tmp_path/(negative+'.stderr');path.write_text(path.read_text().replace(PREFIX[family],'wrong-phase '));d['cases'][negative]['stderr_sha256']=v.sha(path)
 with pytest.raises((ValueError,AssertionError,KeyError)):getattr(v,'verify_'+family)(tmp_path,t,d)

@pytest.mark.parametrize('path',['../outside','/etc/passwd','a/../../outside'])
def test_escape(tmp_path,path):
 with pytest.raises(ValueError):v.safe_file(tmp_path,path)
def test_symlink(tmp_path):
 out=tmp_path/'real';out.write_text('x');(tmp_path/'link').symlink_to(out)
 with pytest.raises(ValueError):v.safe_file(tmp_path,'link')
 with pytest.raises(ValueError):e.inventory(tmp_path)
def test_missing_artifact(tmp_path):
 with pytest.raises(ValueError):v.safe_file(tmp_path,'missing')
def complete():
 return {'pending':[],'families':[{'family':x,'cpu_identity':{'deviceType':4},'run_id':str(uuid.uuid4())} for x in e.FAMILIES],'steps':[{'label':x,'returncode':0,'timed_out':False,'cancelled':False,'budget_exhausted':False,'unexpected_descendants':False,'group_cleanup':{'group_gone':True}} for x in e.FAMILIES]}
@pytest.mark.parametrize('mutation',['missingstep','missingfamily','wrongorder','uuidreuse','timeout','cleanup'])
def test_total_gate(mutation):
 r=complete();e.require_complete(r)
 if mutation=='missingstep':r['steps'].pop()
 elif mutation=='missingfamily':r['families'].pop()
 elif mutation=='wrongorder':r['steps'].reverse()
 elif mutation=='uuidreuse':r['families'][1]['run_id']=r['families'][0]['run_id']
 elif mutation=='timeout':r['steps'][1]['timed_out']=True
 else:r['steps'][1]['group_cleanup']['group_gone']=False
 with pytest.raises(ValueError):e.require_complete(r)
def test_config_commands_rejected(tmp_path):
 p=tmp_path/'config.json';p.write_text(json.dumps({'command':'anything'}))
 with pytest.raises(ValueError):e.config(p)

@pytest.mark.parametrize('family,needle',[('device_address','Aligned 16'),('device_address','OpConvertUToPtr'),('ray_query','OpRayQueryProceedKHR')])
def test_shader_structure_tamper(family,needle):
 valid={
 'device_address':'OpCapability PhysicalStorageBufferAddresses\nOpMemoryModel PhysicalStorageBuffer64 GLSL450\nOpCapability Int64\nOpExecutionMode %main LocalSize 8 1 1\nOpMemberDecorate %PointerTable 0 Offset 0\nOpMemberDecorate %PointerTable 1 Offset 8\nOpConvertUToPtr\nAligned 16\nAligned 8\nAligned 4\nOpDecorate %_runtimearr_uint ArrayStride 4',
 'ray_query':'OpCapability RayQueryKHR\nOpRayQueryInitializeKHR\nOpRayQueryProceedKHR\nOpRayQueryGetIntersectionTypeKHR\nOpRayQueryGetIntersectionTKHR\nOpRayQueryGetIntersectionPrimitiveIndexKHR\nOpExecutionMode %main LocalSize 1 1 1'}[family]
 v.verify_shader_structure(family,valid)
 with pytest.raises(ValueError):v.verify_shader_structure(family,valid.replace(needle,'REMOVED'))
def test_pending_and_boolean_returncode_rejected():
 r=complete();e.require_complete(r);r['pending']=['headless_wsi']
 with pytest.raises(ValueError):e.require_complete(r)
 r=complete();r['steps'][0]['returncode']=False
 with pytest.raises(ValueError):e.require_complete(r)

def test_cross_family_identity():
 r=complete();e.require_complete(r);r['families'][2]['cpu_identity']={'deviceType':2}
 with pytest.raises(ValueError):e.require_complete(r)

def test_final_inventory_failure_no_success_summary(tmp_path,monkeypatch):
 r=complete();r.update(status='BOUNDED_RESOURCE_SUITE_VERIFIED');(tmp_path/'SUMMARY.md').write_text('obsolete success')
 monkeypatch.setattr(e,'inventory',lambda path:(_ for _ in ()).throw(ValueError('injected inventory failure')))
 e.finalize_summary(r,tmp_path)
 assert r['status']=='BLOCKED' and 'Incomplete' in (tmp_path/'SUMMARY.md').read_text() and 'obsolete success' not in (tmp_path/'SUMMARY.md').read_text()

def test_robust_spirv_order_and_atomic():
 text='\n'.join(['OpExecutionMode %main LocalSize 1 1 1','OpMemberDecorate %Params 0 Offset 0']+[f'OpDecorate %{name} Binding {i}\nOpDecorate %{name} DescriptorSet 0' for i,name in enumerate(('src','dst','nil'))]+['%a = OpAccessChain %ptr %src %zero','%b = OpAccessChain %ptr %nil %zero','%l0 = OpLoad %uint %a','%l1 = OpLoad %uint %a','%l2 = OpLoad %uint %a','%l3 = OpLoad %uint %b','OpStore %a %value','OpStore %b %value'])
 v.verify_shader_structure('robust_buffer',text)
 for bad in (text+'\nOpAtomicIAdd',text.replace('Binding 2','Binding 9'),text.replace('OpStore %a %value','').replace('%l0 = OpLoad','OpStore %a %value\n%l0 = OpLoad')):
  with pytest.raises(ValueError):v.verify_shader_structure('robust_buffer',bad)

def test_fixed_spec_rejected_before_parse(tmp_path):
 p=tmp_path/'spec.json';p.write_text('{}')
 with pytest.raises(ValueError,match='fixed normative'):v.verify_normative(tmp_path,p,{'spec_version':{}})
