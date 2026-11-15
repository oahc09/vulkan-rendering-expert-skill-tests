import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_near_clip_lab/run_lab.py'
def test_actual_world_glyph_near_clip(tmp_path):
 if os.environ.get('VULKAN_TEXT18_NEAR_CLIP')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==3
 assert all(x['max_composition_error']<=1e-6 and x['excluded_count']==0 for x in r['cases'])
 assert r['cases'][2]['glyph_roi_pixels']==0 and r['cases'][0]['glyph_roi_pixels']>0 and r['cases'][1]['glyph_roi_pixels']>0
 assert len(r['hardware_nearest_cases'])==3
 assert r['hardware_nearest_status'] in ('NOT_QUALIFIED','PASS_ON_THIS_RUN')
 assert r['stable_sampler_max_integer_magnitude']<2**31
 assert r['uv_diagnostic']['exact_source_fractions'][1]=='3'
 assert r['uv_diagnostic']['max_depth_preservation_error']<=1e-6
 assert len(r['actual_gpu_negatives'])==2 and len(r['input_rejections_before_gpu'])==2
