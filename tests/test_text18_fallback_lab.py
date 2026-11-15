import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_multiface_run_fallback(tmp_path):
 if os.environ.get('VULKAN_TEXT18_FALLBACK')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/text_fallback_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled']
 assert r['numeric']['max_linear_error']<=1e-6 and r['run_count']==4 and r['selected_face_count']==3
 assert r['missing_final_rejected'] and r['actual_wrong_route_rejected']
