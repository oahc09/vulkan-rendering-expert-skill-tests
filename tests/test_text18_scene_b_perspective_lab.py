import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('TEXT18_SCENE_B_PERSPECTIVE')!='1',reason='opt-in actual integrated perspective Vulkan')
def test_actual_shared_perspective_scene(tmp_path):
 out=tmp_path/'actual';p=Path(__file__).parent/'fixtures/scene_b_perspective_lab/run_lab.py';r=subprocess.run([sys.executable,str(p),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','--out',str(out)],capture_output=True,text=True,timeout=300);(tmp_path/'run.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
 s=json.loads((out/'summary.json').read_text());assert s['status']=='PASS' and s['validation_enabled'] and s['excluded']==0
 assert set(s['variants'])=={'baseline','near-cross','reflected','wrong-near','wrong-caster-model'}
 for key in ('baseline','near-cross','reflected'):
  v=s['variants'][key];assert v['shadow_depth_error']<=1e-6 and len(v['views'])==12
  for row in v['views'].values():assert row['depth_error']<=1e-6 and (row['color_error']<=1e-6)==row['positive_view']
 for name in ('A','B'):
  assert s['variants']['wrong-near']['views'][name]['depth_error']>1e-6
  assert s['variants']['wrong-caster-model']['views'][name]['depth_error']<=1e-6
 assert s['variants']['wrong-caster-model']['shadow_depth_error']>1e-6
