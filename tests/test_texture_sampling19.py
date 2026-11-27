import importlib.util,pathlib,pytest,json
P=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('sampling',P/'tools/texture_sampling19.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def good():return dict(minFilter=0,magFilter=0,mipmapMode=0,addressU=2,addressV=2,addressW=2,minLod=0,maxLod=0,unnormalized=0,anisotropyEnable=0,compareEnable=0)
def test_good_negative():
 assert m.sampler(good())['status']=='NEAREST_CLAMP_SCOPE';bad=good();bad.update(unnormalized=1,mipmapMode=1);assert m.sampler(bad)==dict(status='REJECTED',vuids=[m.VUID])
@pytest.mark.parametrize('key',list(good()))
def test_unknown(key):
 p=good();p.pop(key);assert m.sampler(p)['status']=='UNKNOWN'
@pytest.mark.parametrize('value',[True,None,float('nan'),float('inf'),'0'])
def test_bad_type(value):
 p=good();p['addressU']=value;assert m.sampler(p)['status']=='UNKNOWN'
def test_not_transpose_or_flip():
 p=m.reference();assert len(p)==16;assert p!=[p[x*4+y] for y in range(4) for x in range(4)];assert p!=list(reversed(p));assert len(set(p))>2
 assert p[0]==p[1] # negative-u clamp
 assert p[8:12]==p[12:16] # high-v clamp
 assert [v^1 for v in p]!=p
@pytest.mark.parametrize('key,value',[('minFilter',1),('maxLod',1),('addressU',0),('unnormalized',3)])
def test_out_of_scope(key,value):
 p=good();p[key]=value;assert m.sampler(p)['status']=='OUT_OF_SCOPE'
def test_normative_entry():
 j=json.loads((P/'cases19/texture_sampling/normative.json').read_text());assert j['api_version']=='1.4.309';assert j['entries'][0]['vuid']==m.VUID
