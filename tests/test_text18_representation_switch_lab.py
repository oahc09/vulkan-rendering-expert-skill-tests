import importlib.util,json,os,subprocess,sys
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_representation_switch_lab/run_lab.py'
@pytest.mark.host_unit
def test_switch_holds_previous_state_inside_band():
 s=importlib.util.spec_from_file_location('switch',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 assert [r['selected'] for r in m.routes()]==[0,0,0,1,1,1,0,0,0,1]
 assert m.routes()[2]['selected']!=m.routes()[4]['selected'] # same1.05, distinct preceding state
@pytest.mark.vulkan_integration
def test_actual_stateful_same_device_representation_switch(tmp_path):
 if os.environ.get('VULKAN_TEXT18_REPRESENTATION_SWITCH')!='1':pytest.skip('explicit trusted MSDF switch experiment opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE required')
 out=tmp_path/'switch'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=360)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='MEASURED_NOT_QUALIFIED' and len(r['frames'])==10
 assert r['wrong_hold_pixel_error']>1e-6
