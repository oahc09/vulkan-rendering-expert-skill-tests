import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.dynamic_color19 import admit,content

def config():return dict(offsetX=0,offsetY=0,samples=1,layers=1,viewMask=0,resolveMode=0,supported=1,enabled=1,format=37,usage=17,viewWidth=4,viewHeight=4,width=4,height=4,layout=2,loadOp=1,storeOp=0)
def test_good():assert admit(config())['status']=='CONFIG_WITHIN_SCOPE'
@pytest.mark.parametrize('key,val,vuid',[('enabled',0,'VUID-vkCmdBeginRendering-dynamicRendering-06446'),('usage',1,'VUID-VkRenderingInfo-colorAttachmentCount-06087'),('width',5,'VUID-VkRenderingInfo-pNext-06079'),('height',5,'VUID-VkRenderingInfo-pNext-06080'),('width',0,'VUID-VkRenderingInfo-None-08994'),('height',0,'VUID-VkRenderingInfo-None-08995'),('layout',6,'VUID-VkRenderingAttachmentInfo-imageView-06135')])
def test_invalid(key,val,vuid):
 m=config();m[key]=val;assert admit(m)['vuids']==[vuid]
@pytest.mark.parametrize('key,val,status',[('supported',0,'UNSUPPORTED'),('format',99,'OUT_OF_SCOPE'),('layout',100,'OUT_OF_SCOPE'),('storeOp',100,'OUT_OF_SCOPE')])
def test_unknown(key,val,status):
 m=config();m[key]=val;assert admit(m)['status']==status
def test_missing():assert admit({})['status']=='UNKNOWN'
def test_bool():
 m=config();m['enabled']=True
 with pytest.raises(ValueError):admit(m)
@pytest.mark.parametrize('load,store,prior,expected',[(1,0,False,'DEFINED'),(0,0,True,'DEFINED'),(0,0,False,'UNDEFINED'),(1,1,True,'UNDEFINED'),(2,0,True,'UNDEFINED')])
def test_content(load,store,prior,expected):assert content(load=load,store=store,prior_defined=prior,dependency_proven=True,full_region=True)['status']==expected
@pytest.mark.parametrize('key,status',[('dependency_proven','UNKNOWN_DEPENDENCY'),('full_region','UNKNOWN_SUBREGION')])
def test_bound(key,status):
 d=dict(load=0,store=0,prior_defined=True,dependency_proven=True,full_region=True);d[key]=False;assert content(**d)['status']==status

@pytest.mark.parametrize('key,val',[('offsetX',1),('offsetY',1),('samples',4),('layers',2),('viewMask',1),('resolveMode',1)])
def test_scope(key,val):
 m=config();m[key]=val;assert admit(m)['status']=='OUT_OF_SCOPE'
@pytest.mark.parametrize('key',['offsetX','offsetY','samples','layers','viewMask','resolveMode'])
def test_scope_missing(key):
 m=config();del m[key];assert admit(m)['status']=='UNKNOWN'

def test_retained_actual_cohort_source_pair():
 import json,hashlib
 root=pathlib.Path(__file__).resolve().parents[1]
 r=json.loads((root/'coverage/v1.0.19/dynamic-color.json').read_text())
 for key,path in [('source_sha256','cases19/dynamic_color/probe.c'),('runner_sha256','cases19/dynamic_color/run.py'),('rules_sha256','tools/dynamic_color19.py')]:
  assert r[key]==hashlib.sha256((root/path).read_bytes()).hexdigest()
 assert r['status']=='BOUNDED_DYNAMIC_COLOR_PASS'
 assert r['spec_version']['api version']=='1.4.309'
 assert set(r['cases'])=={'good','area','layout','feature','wrong-output'}
 for mode,case in r['cases'].items():
  ex=case['records']['execution']
  if mode in ('good','wrong-output'):
   assert ex['pixels']==[[255,0,255,255]]*16 and ex['fenceCompleted'] is True
   assert [s['status'] for s in case['content']]==['DEFINED','DEFINED']
   assert case['exit_code']==(6 if mode=='wrong-output' else 0)
  else:
   assert ex=={'kind':'execution','submitted':False,'discarded':True}
   assert case['admission']['vuids']==[case['normative']['vuid']]
 # Retained same-source execution, not a newly invoked device test.
