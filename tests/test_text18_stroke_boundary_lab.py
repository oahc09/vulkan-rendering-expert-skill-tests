import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_stroke_boundary_lab/run_lab.py'
def test_actual_closed_stroke_boundary_fallback(tmp_path):
 if os.environ.get('VULKAN_TEXT18_STROKE_BOUNDARY')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==9
 assert all(c['excluded_count']==0 and c['max_all_pixel_color_depth_error']<=1e-6 for c in r['cases'])
 assert len(r['actual_gpu_negatives'])==3 and all(c['mismatch_pixels'] for c in r['actual_gpu_negatives'])
 assert len(r['omitted_fallback_original_mesh'])==3 and all(c['mismatch_pixels'] for c in r['omitted_fallback_original_mesh'])
