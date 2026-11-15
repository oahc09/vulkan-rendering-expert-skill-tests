import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_shadow_lab/run_lab.py'
def test_actual_shaped_shadow_producer_consumer(tmp_path):
 if os.environ.get('VULKAN_TEXT18_SHADOW')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled']
 assert r['cases']['normal']['max_shadow_depth_error']<=1e-6 and r['cases']['normal']['max_composition_error']<=1e-6
 assert all(v['receiver_depth_error']<=1e-6 for v in r['cases'].values())
 assert r['cases']['bypass']['max_composition_error']>1e-6 and r['cases']['wrong-caster']['max_shadow_depth_error']>1e-6
