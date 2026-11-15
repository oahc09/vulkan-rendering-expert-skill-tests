import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_dual_pending_lab/run_lab.py'
def test_actual_dual_device_pending_isolation(tmp_path):
 if os.environ.get('VULKAN_TEXT18_DUAL_PENDING')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and r['logical_devices']==2 and r['B_positive_images']==3
 s=importlib.util.spec_from_file_location('dual_pending',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'frames',bad/'frames');shutil.copyfile(out/'reference.json',bad/'reference.json');shutil.copytree(out/'new-reference',bad/'new-reference');shutil.copyfile(out/'frames/B-initial-A-pending/color.rgba32f',bad/'frames/B-new-A-pending/color.rgba32f')
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
 bad2=tmp_path/'bad2';shutil.copytree(out/'frames',bad2/'frames');(bad2/'frames/events.jsonl').write_text((bad2/'frames/events.jsonl').read_text().replace('"A_pending":true','"A_pending":false',1))
 with pytest.raises(ValueError,match='event mismatch'):m.verify(bad2)
