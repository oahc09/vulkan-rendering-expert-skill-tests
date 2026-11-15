import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_second_camera_lab/run_lab.py'
def test_actual_second_camera_same_device(tmp_path):
 if os.environ.get('VULKAN_TEXT18_SECOND_CAMERA')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==4
 assert all(c['max_composition_error']<=1e-6 and c['excluded_count']==0 for c in r['cases'])
 assert r['device_instances']==r['world_vertex_buffers']==r['shared_atlas_images']==1
 assert r['actual_gpu_negative']['max_composition_error']>1e-6
