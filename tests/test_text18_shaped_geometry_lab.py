import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_shaped_geometry_lab/run_lab.py'
def test_actual_shaped_glyph_geometry_or_fallback(tmp_path):
 if os.environ.get('VULKAN_TEXT18_SHAPED_GEOMETRY')!='1':pytest.skip('explicit trusted Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and len(r['mesh'])==1 and r['enclosed_hole_pixels']>0
 assert r['mesh'][0]['max_color_error']<=1e-6 and r['mesh'][0]['max_depth_error']<=1e-6 and r['fallback']['max_linear_error']<=1e-6
