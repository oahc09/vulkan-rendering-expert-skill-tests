import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('TEXT18_SCENE_B_VECTOR')!='1',reason='opt-in shared world vector Vulkan')
def test_actual_shared_world_vector(tmp_path):
 out=tmp_path/'actual';p=Path(__file__).parent/'fixtures/scene_b_vector_overlay_lab/run_lab.py';r=subprocess.run([sys.executable,str(p),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','--out',str(out)],capture_output=True,text=True,timeout=240);(tmp_path/'run.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
 s=json.loads((out/'summary.json').read_text());assert s['status']=='PASS' and s['validation_enabled'];assert s['positive_views']==5 and s['negative_views']==7 and len(s['cases'])==12
 assert s['shadow_depth_error']<=1e-6 and s['excluded']==0
 for row in s['cases'].values():assert row['depth_error']<=1e-6 and (row['color_error']<=1e-6)==row['positive']
