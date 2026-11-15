import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_resident_scene_c_service(tmp_path):
 if os.environ.get('TEXT18_SCENE_C_SERVICE')!='1':pytest.skip('explicit resident CPU/Vulkan scene service opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/scene_c_service_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['validation_enabled'] and len(r['rows'])==7
 assert r['protocol_pending_cleanup_negatives']==2 and r['native_page_capacity_rejected'] and r['bad_write_rejected_images']==8
 assert r['trace'][8]['after_ack_seq']==1 and r['trace'][8]['ft_delta']==1 and r['trace'][9]['after_ack_seq']==4 and r['trace'][9]['ft_delta']==0
