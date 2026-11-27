import importlib.util,json,os,subprocess,sys
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_msdf_cost_lab/run_lab.py'
@pytest.mark.host_unit
def test_cost_nearest_rank_fixed_quantiles():
 s=importlib.util.spec_from_file_location('cost',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 assert m.percentile(list(range(1,31)),.5)==15
 assert m.percentile(list(range(1,31)),.95)==29
 with pytest.raises(ValueError):m.percentile([], .5)
 with pytest.raises(ValueError):m.percentile([float('nan')],.5)
@pytest.mark.vulkan_integration
def test_software_msdf_cost_measurement(tmp_path):
 if os.environ.get('VULKAN_TEXT18_MSDF_COST')!='1':pytest.skip('explicit local cost experiment opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE required')
 out=tmp_path/'cost'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=600)
 r=json.loads((out/'summary.json').read_text())
 if r['status']=='NOT_MEASURED':pytest.skip('timestamp unsupported; explicit evidence retained')
 assert r['status']=='MEASURED_SOFTWARE_ONLY' and len(r['modes'])==3
 assert all(x['timestampValidBits']>0 and x['timestampPeriod']>0 for x in r['capabilities'])
