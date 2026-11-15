import importlib.util,json,os,subprocess,sys
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_msdf_integration_lab/run_lab.py'
def module():
 s=importlib.util.spec_from_file_location('msdf_integrated',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.host_unit
def test_exact_polygon_area_and_clipping():
 m=module();rect=[(0,0),(2,0),(2,2),(0,2)]
 assert m.exact([rect],0,0)==1
 assert m.exact([rect],2,0)==0
 assert m.exact([rect],1.5,0)==pytest.approx(.5)
 assert m.exact([[(0,0),(1,0),(0,1)]],0,0)==pytest.approx(.5)
@pytest.mark.host_unit
def test_exact_opposite_winding_hole():
 m=module();outer=[(0,0),(1,0),(1,1),(0,1)];hole=[(.25,.25),(.25,.75),(.75,.75),(.75,.25)]
 assert m.exact([outer,hole],0,0)==pytest.approx(.75)
@pytest.mark.vulkan_integration
def test_gpu_msdf_subpixel_integration(tmp_path):
 if os.environ.get('VULKAN_TEXT18_MSDF_INTEGRATION')!='1':pytest.skip('explicit expensive software Vulkan experiment opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE required')
 out=tmp_path/'integration'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=360)
 result=json.loads((out/'comparison.json').read_text())
 assert result['status']=='MEASURED_NOT_QUALIFIED' and result['samples_per_pixel']=={'binary16':256,'linear4':16}
 assert len(result['rows'])==16 and all(v>.004 for v in result['negative_srgb_sampling_error'].values())
 assert all(r['max_error']<r['baseline']['max_coverage_error'] for r in result['rows'])
