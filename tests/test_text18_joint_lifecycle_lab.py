import os,sys,json,subprocess,importlib.util,shutil
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_JOINT_LIFECYCLE')!='1',reason='opt-in actual joint lifecycle')
def test_actual_joint_lifecycle(tmp_path):
 runner=Path(__file__).parent/'fixtures/text_joint_lifecycle_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out)],check=True,capture_output=True,text=True,timeout=240)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and s['active_color_attachments']==3 and len(s['rows'])==3
 assert min(s['conditions']['clip_bypass_nonzero_pixels'])>0 and s['conditions']['positive_nonzero_pixels']>0
 spec=importlib.util.spec_from_file_location('joint',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad'
 shutil.copytree(out/'frames',bad/'frames');shutil.copyfile(out/'reference.json',bad/'reference.json');shutil.copytree(out/'new-reference',bad/'new-reference')
 p=bad/'frames/new-B/color.rgba32f';p.write_bytes((bad/'frames/old-A/color.rgba32f').read_bytes())
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
 p.write_bytes((out/'frames/new-B/color.rgba32f').read_bytes());p=bad/'frames/events.jsonl';events=[json.loads(x) for x in p.read_text().splitlines()];events[0]['published']=1;p.write_text('\n'.join(map(json.dumps,events)))
 with pytest.raises(ValueError,match='events mismatch'):m.verify(bad)
