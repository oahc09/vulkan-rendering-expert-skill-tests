import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_world_label_lab/run_lab.py'
def test_actual_world_glyph_perspective(tmp_path):
 if os.environ.get('VULKAN_TEXT18_WORLD_LABEL')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==4
 assert all(x['max_composition_error']<=1e-6 and x['excluded_count']==0 for x in r['cases'])
 assert len(r['actual_gpu_negatives'])==2 and len(r['input_rejections_before_gpu'])==2
 assert r['cases'][0]['glyph_roi_pixels']>r['cases'][2]['glyph_roi_pixels']
