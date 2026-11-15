import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_stroke_area_lab/run_lab.py'
def test_actual_stroke_exact_area_aa(tmp_path):
 if os.environ.get('VULKAN_TEXT18_STROKE_AREA')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==16
 assert all(c['max_composition_depth_error']<=1e-6 and c['max_alpha_inferred_coverage_error']<=1e-6 and c['excluded_count']==0 for c in r['cases'])
 assert all(c['partial_pixels']>0 for c in r['cases'] if c['name']!='horizontal-square-1')
 assert next(c for c in r['cases'] if c['name']=='horizontal-square-1')['partial_pixels']==0
 assert all(c['max_depth_preservation_error']==0 for c in r['cases']+r['actual_gpu_negatives'])
 assert len(r['actual_gpu_negatives'])==2
