import sys,pathlib,pytest,copy,importlib.util,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.device_selection19 import select,match

def caps():return {'loaderApi':4206592,'devices':[dict(deviceType=4,deviceID=0,vendorID=1,driverVersion=1,apiVersion=4206592,dynamicRenderingSupported=1,formatResult=0,formatWidth=4,formatHeight=4,formatSamples=1,maxDrawIndirectCount=1,maxColorAttachments=1,maxFramebufferWidth=4,maxFramebufferHeight=4,maxViewportWidth=4,maxViewportHeight=4,maxComputeInvocations=1,maxLocalX=1,maxGroupsX=1,viewportBoundsMin=-16,viewportBoundsMax=16,coherentHostTypeExists=1,queues=[dict(family=0,flags=3,count=1)])]}
def test_good():assert select(caps())['status']=='ADMITTED_SUPPORT_ONLY'
def test_profile():assert select(caps(),'unknown')['status']=='REJECTED_PROFILE'
@pytest.mark.parametrize('n',[0,2])
def test_count(n):
 c=caps();c['devices']=c['devices']*n;assert select(c)['status']=='REJECTED_DEVICE_SCOPE'
@pytest.mark.parametrize('k,v',[('dynamicRenderingSupported',0),('apiVersion',4194304),('formatWidth',3),('maxDrawIndirectCount',0),('maxComputeInvocations',0)])
def test_requirements(k,v):
 c=caps();c['devices'][0][k]=v;assert select(c)['status']=='UNAVAILABLE_REQUIREMENTS'
def test_missing():assert select({})['status']=='UNKNOWN'
def test_bool():
 c=caps();c['devices'][0]['apiVersion']=True;assert select(c)['status']=='UNKNOWN'
@pytest.mark.parametrize('k',['deviceID','vendorID','driverVersion','apiVersion','queueFamily','queueFlags'])
def test_identity(k):
 a=select(caps());i={**a['identity'],'queueFamily':0,'queueFlags':3};match(a,i);i[k]+=1
 with pytest.raises(ValueError):match(a,i)

@pytest.mark.parametrize('key,val',[('apiVersion',1<<29|4206592),('deviceID',-1),('apiVersion',1<<32),('queues',[None]),('queues',[dict(family=1,flags=3,count=1)])])
def test_unknown_facts(key,val):
 c=caps();c['devices'][0][key]=val;assert select(c)['status']=='UNKNOWN'

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scene_entry_test',ROOT/'checks19/run_indirect_scene.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
@pytest.mark.parametrize('mutation,message',[('usage','rejected configuration'),('dispatch','dispatch mismatch'),('dependency','dependency mismatch'),('identity','different physical identity'),('memory','memory selection'),('missing',None),('empty-tools','missing shader tool'),('wrong-source','source report binding'),('loader','tool cohort mismatch'),('layer','layer runtime mismatch'),('spec','spec version mismatch'),('zero-init','initial argument state')])
def test_raw_coordinated_mutation(tmp_path,mutation,message):
 r=json.loads((ROOT/'coverage/v1.0.19/indirect-draw.json').read_text());identity=r['cases']['good']['records']['identity'];a={'status':'ADMITTED_SUPPORT_ONLY','identity':{k:identity[k] for k in ('deviceType','deviceID','vendorID','driverVersion','apiVersion')},'queue':{'family':identity['queueFamily'],'flags':identity['queueFlags']}}
 from tools import device_selection19,dynamic_color19,dynamic_draw19
 def materialize():
  for name,case in r['cases'].items():
   out=tmp_path/(name+'.stdout');err=tmp_path/(name+'.stderr');out.write_text('\n'.join(json.dumps(x) for x in case['records'].values())+'\n');err.write_text('\n'.join(case['diagnostics'])+('\n' if case['diagnostics'] else ''));case['stdout_sha256']=entry.sha(out);case['stderr_sha256']=entry.sha(err)
  for stage,shader in r['shaders'].items():
   spv=tmp_path/(stage+'.spv');spv.write_bytes(b'fixture');shader['binary_sha256']=entry.sha(spv)
   for name,tool in shader['tools'].items():
    for stream in ('stdout','stderr'):
     log=tmp_path/(stage+'-'+name+'.'+stream);log.write_bytes(b'fixture');tool[stream+'_sha256']=entry.sha(log)
  probe=tmp_path/'probe';probe.write_bytes(b'fixture');r['binary_sha256']=entry.sha(probe);(tmp_path/'summary.json').write_text(json.dumps(r))
 tools=tmp_path/'tools';tools.mkdir();tc={'tools':str(tools),'loader':str(tmp_path/'loader'),'icd':str(tmp_path/'icd'),'layer_path':str(tmp_path),'validusage':str(tmp_path/'validusage')}
 for name in ('glslangValidator','spirv-val','spirv-dis'):(tools/name).write_bytes(b'fixture-tool')
 for name in ('loader','icd'):(tmp_path/name).write_bytes(b'fixture-manifest')
 (tmp_path/'VkLayer_khronos_validation.json').write_text(json.dumps({'layer':{'api_version':'1.4.309','implementation_version':'1'}}));(tmp_path/'validusage').write_text(json.dumps({'version info':r['spec_version']}))
 for key,path in {'loader_sha256':tc['loader'],'icd_manifest_sha256':tc['icd'],'layer_manifest_sha256':tmp_path/'VkLayer_khronos_validation.json','spec_sha256':tc['validusage']}.items():r[key]=entry.sha(path)
 for shader in r['shaders'].values():
  for tool in shader['tools'].values():tool['tool_sha256']=entry.sha(tools/'spirv-val')
 materialize();entry.raw_verify(tmp_path,(device_selection19,a),tc)  # complete positive baseline, not a missing-file false negative
 c=r['cases']['good'];rec=c['records']
 if mutation=='usage':rec['manifest']['usage']=1;c['attachment_admission']=dynamic_color19.admit(rec['manifest']);c['admission']=dynamic_draw19.admit(rec['pipeline'],rec['manifest'],rec['limits'])
 if mutation=='dispatch':rec['compute']['dispatched']=False
 if mutation=='dependency':rec['generation_dependency']['srcAccess']=0
 if mutation=='identity':rec['identity']['deviceID']+=1
 if mutation=='memory':rec['indirect_allocation']['selectedFlags']=0
 if mutation=='missing':del rec['compute']
 if mutation=='empty-tools':r['shaders']['vert']['tools']={}
 if mutation=='wrong-source':r['source_sha256']='0'*64
 if mutation=='loader':r['loader_sha256']='0'*64
 if mutation=='layer':rec['identity']['layerImplementation']+=1
 if mutation=='spec':r['spec_version']={}
 if mutation=='zero-init':rec['indirect_allocation']['initializedZeroBytes']=0
 materialize()
 with pytest.raises((ValueError,KeyError),match=message):entry.raw_verify(tmp_path,(device_selection19,a),tc)
def test_unknown_toolchain_keys(tmp_path):
 p=tmp_path/'cfg.json';p.write_text(json.dumps({'command':'echo bad'}))
 with pytest.raises(ValueError):entry.config(p)

def test_non_object_device():assert select({'devices':[None]})['status']=='UNKNOWN'
def test_overwide_queue():
 c=caps();c['devices'][0]['queues'][0]['count']=1<<32;assert select(c)['status']=='UNKNOWN'
