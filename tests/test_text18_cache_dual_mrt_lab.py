import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_cache_dual_device_active_mrt(tmp_path):
 if os.environ.get('TEXT18_CACHE_DUAL_MRT')!='1':pytest.skip('explicit dual-device active MRT cache opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/font_cache_dual_mrt_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled'] and len(r['rows'])==6
 assert r['simultaneously_live_devices']==2 and r['logical_devices_created']==3 and r['active_color_attachments']==3 and r['bad_write_rejected_images']==7
