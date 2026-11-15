import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_stroke_lab/run_lab.py'
def test_actual_bounded_stroke_caps_joins(tmp_path):
 if os.environ.get('VULKAN_TEXT18_STROKE')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['cases'])==6 and len(r['input_rejections_before_gpu'])==7
 assert r['mesh_receipts']['miter-limited']['effective_join']=='bevel' and r['mesh_receipts']['miter-accepted']['effective_join']=='miter'
 assert all(row['max_unexcluded_error']<=1e-6 for row in r['cases'])
