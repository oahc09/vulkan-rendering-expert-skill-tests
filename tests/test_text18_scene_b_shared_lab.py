import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('TEXT18_SCENE_B_SHARED')!='1',reason='opt-in actual software Vulkan shared scene')
def test_actual_shared_world_scene(tmp_path):
 out=tmp_path/'actual';p=Path(__file__).parent/'fixtures/scene_b_shared_world_lab/run_lab.py'
 r=subprocess.run([sys.executable,str(p),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','--out',str(out)],capture_output=True,text=True,timeout=240)
 (tmp_path/'run.log').write_text(r.stdout+r.stderr)
 assert r.returncode==0,r.stdout+r.stderr
 s=json.loads((out/'summary.json').read_text());assert s['status']=='PASS' and s['validation_enabled']
 assert s['shadow_depth_error']<=1e-6 and s['excluded']==0
 assert set(s['cases'])=={'A','B','B-no-shadow','B-stale-label'}
 for name,row in s['cases'].items():
  assert row['depth_error']<=1e-6 and all(v>0 for v in row['roi'].values())
  assert (row['color_error']<=1e-6)==(name in ('A','B'))
