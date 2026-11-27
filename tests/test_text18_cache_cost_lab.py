import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration # existing opt-in environment cohort; this test is CPU ONLY

def test_actual_cpu_cache_cost(tmp_path):
 if os.environ.get('TEXT18_CACHE_COST')!='1':pytest.skip('explicit actual CPU font provider opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/font_cache_cost_lab/run_lab.py'),'--out',str(out)],check=True,timeout=120)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and len(r['rounds'])==12
 assert all(x['hot_ft_calls']==x['hot_hb_calls']==0 for x in r['rounds'])
 assert r['final_owned_coverage_bytes']==0 and r['eviction_reproduces'] and r['caller_mutation_isolated']
