import os,sys,json,subprocess,shutil,importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_DUAL_DEVICE')!='1',reason='opt-in two logical devices')
def test_actual_dual_device_lifecycle(tmp_path):
 runner=Path(__file__).parent/'fixtures/text_dual_device_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,capture_output=True,text=True,timeout=180)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and len(s['rows'])==8 and s['logical_devices_created']==3
 spec=importlib.util.spec_from_file_location('dual',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'inputs',bad/'inputs');shutil.copytree(out/'frames',bad/'frames')
 target=bad/'frames/B-A-destroyed/gpu/color.rgba32f';good=target.read_bytes();target.write_bytes((bad/'frames/B-initial/gpu/color.rgba32f').read_bytes())
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
 target.write_bytes(good);p=bad/'frames/events.jsonl';events=[json.loads(x) for x in p.read_text().splitlines()];events[2]['live']=2;p.write_text('\n'.join(map(json.dumps,events)))
 with pytest.raises(ValueError,match='lifecycle mismatch'):m.verify(bad)
