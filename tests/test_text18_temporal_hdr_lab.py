import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_temporal_hdr_text_consumer(tmp_path):
 if os.environ.get('VULKAN_TEXT18_TEMPORAL_HDR')!='1':pytest.skip('explicit temporal/HDR UI opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/text_temporal_hdr_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled'] and r['paired_ui_history_byte_equal']
 assert len(r['cases']['ui-O'])==4 and all(x['consumer_error']<=1e-6 for x in r['cases']['ui-O'])
