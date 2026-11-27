import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_cache_products_gpu_churn(tmp_path):
 if os.environ.get('TEXT18_CACHE_CHURN')!='1':pytest.skip('explicit actual GPU cache churn opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/font_cache_churn_lab/run_lab.py'),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and r['status']=='PASS' and len(r['rows'])==18
 assert r['cpu_final_owned_coverage_bytes']==0 and r['wrong_resource_route_rejected'] and r['retirement_record_negative_rejected']
 assert [x['raster_calls'] for x in r['cpu_input_audit']]==[1,0,1,0,1,0,1]
