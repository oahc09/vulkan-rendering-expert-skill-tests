import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_lifecycle_handoff_lab/run_lab.py'
def test_actual_pending_lifecycle_with_scene_handoff(tmp_path):
 if os.environ.get('VULKAN_TEXT18_LIFECYCLE_HANDOFF')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and r['positive_verified_images']==3 and r['draws_per_render_submission']==3
 s=importlib.util.spec_from_file_location('handoff_life',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'frames',bad/'frames');shutil.copyfile(out/'reference.json',bad/'reference.json');shutil.copytree(out/'new-reference',bad/'new-reference');shutil.copyfile(out/'frames/old-A/color.rgba32f',bad/'frames/new-B/color.rgba32f')
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
