"""Host mutations of recorded actual facts; not new Vulkan runs."""
import copy,importlib.util,json,pathlib,pytest
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('comparison_test',ROOT/'checks19/compare_depth_samples.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def rewrite(tmp,r):
 for mode,c in r['cases'].items():
  (tmp/(mode+'.stdout')).write_text('\n'.join(json.dumps(x) for x in c['records'].values())+'\n');(tmp/(mode+'.stderr')).write_text(''.join(x+'\n' for x in c['diagnostics']))
  for stream in ('stdout','stderr'):c[stream+'_sha256']=m.sha(tmp/(mode+'.'+stream))
 (tmp/'summary.json').write_text(json.dumps(r))
def fixture(tmp,n):
 r=json.loads((ROOT/'tests/fixtures/depth_ab_records.json').read_text())[str(n)];rewrite(tmp,r);m.verify_records(tmp,n,r,dict(implementation_version=1));return r
@pytest.mark.parametrize('n',[1,4])
def test_positive(tmp_path,n):fixture(tmp_path,n)
@pytest.mark.parametrize('mutation',['pixel','depth-disabled-pixel','samplecount','budget','missingreceipt','wrongphase','submitted','shader','sourceidentity','missingmode','testenable','draworder','barrier','cohort','extra-allocation'])
@pytest.mark.parametrize('n',[1,4])
def test_coordinated(tmp_path,n,mutation):
 r=fixture(tmp_path,n);good=r['cases']['good']['records']
 if mutation=='pixel':good['execution']['pixels'][0][0]^=255
 elif mutation=='depth-disabled-pixel':r['cases']['depth-disabled']['records']['execution']['pixels'][0][0]^=255
 elif mutation=='samplecount':good['resolve_contract']['sourceSamples']=4 if n==1 else 1
 elif mutation=='budget':good['allocation_budget']['requestedBytes']+=1
 elif mutation=='missingreceipt':del good['depth_request']
 elif mutation=='wrongphase':r['cases']['depth-format']['diagnostics'][0]=r['cases']['depth-format']['diagnostics'][0].replace('depth-format ','wrong-phase ')
 elif mutation=='submitted':r['cases']['depth-format']['records']['execution']['submitted']=True
 elif mutation=='shader':r['workload']['source_fragment_sha256']='0'*64
 elif mutation=='sourceidentity':good['descriptor']['distinctImages']=False
 elif mutation=='missingmode':del r['cases']['wrong-output']
 elif mutation=='testenable':good['depth_contract']['testEnable']=0;r['cases']['good']['admission']=dict(status='DEPTH_DISABLED_CONTROL',vuids=[])
 elif mutation=='draworder':good['draw_sequence']['modes']=[1,0]
 elif mutation=='barrier':good['depth_transition']['dstAccess']=0
 elif mutation=='extra-allocation':good['extra_request']=dict(kind='extra_request',object='extra',requestedBytes=8,memoryTypeIndex=0);good['extra_allocation']=dict(kind='extra_allocation',size=8,selectedType=0)
 elif mutation=='cohort':r['cases']['wrong-output']['records']['identity']['deviceID']+=1
 rewrite(tmp_path,r)
 with pytest.raises((ValueError,KeyError)):m.verify_records(tmp_path,n,r,dict(implementation_version=1))
def test_symlink(tmp_path):
 (tmp_path/'x').symlink_to('/etc/hosts')
 with pytest.raises(ValueError,match='escape'):m.inventory(tmp_path)
def test_duplicate_json(tmp_path):
 p=tmp_path/'x';p.write_text('{"x":1,"x":2}')
 with pytest.raises(ValueError,match='duplicate'):m.read(p)

def test_root_symlink(tmp_path):
 real=tmp_path/'real';real.mkdir();link=tmp_path/'linked';link.symlink_to(real,target_is_directory=True)
 with pytest.raises(ValueError,match='root symlink'):m.inventory(link)
def test_nested_same_name_included(tmp_path):
 (tmp_path/'child').mkdir();(tmp_path/'child/comparison-index.json').write_text('{}');(tmp_path/'comparison-index.json').write_text('{}')
 assert 'child/comparison-index.json' in m.inventory(tmp_path,exclude_index=True)
 assert 'comparison-index.json' not in m.inventory(tmp_path,exclude_index=True)
 assert 'comparison-index.json' in m.inventory(tmp_path)
