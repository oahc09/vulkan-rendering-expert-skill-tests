import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_real_emoji_selectors(tmp_path):
 if os.environ.get('VULKAN_TEXT18_EMOJI')!='1':pytest.skip('explicit real emoji opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/text_emoji_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled'] and r['png_to_ft_premult_byte_error']==0
 assert r['cases']['vs16']['max_composition_error']<=1e-6 and r['cases']['vs16']['partial_pixels']>0

 assert r["request_routes"]=={"vs16":"emoji","vs15":"text"}
