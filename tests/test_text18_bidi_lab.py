import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_bidi_fallback_paragraph(tmp_path):
 if os.environ.get('VULKAN_TEXT18_BIDI')!='1':pytest.skip('explicit bidi+Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/text_bidi_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled']
 assert r['official_unicode_vectors']==r['independent_icu_map_cases']==2
 assert all(x['numeric']['max_linear_error']<=1e-6 and len(x['negative_checks'])==2 for x in r['cases'])
