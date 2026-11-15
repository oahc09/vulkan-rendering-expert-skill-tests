import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_CONTENT_CHURN')!='1',reason='opt-in actual Vulkan content churn')
def test_actual_content_churn(tmp_path):
 runner=ROOT/'tests/fixtures/text_content_churn_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out),'--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],check=True,timeout=180,capture_output=True,text=True)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and len(s['rows'])==18 and s['rounds']==6
 spec=importlib.util.spec_from_file_location('content_churn',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'inputs',bad/'inputs');shutil.copytree(out/'frames',bad/'frames')
 shutil.copyfile(bad/'frames/1/old/color.rgba32f',bad/'frames/1/new/color.rgba32f')
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
 shutil.copyfile(out/'frames/1/new/color.rgba32f',bad/'frames/1/new/color.rgba32f')
 p=bad/'frames/events.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()];rows[0]['published']=1;p.write_text('\n'.join(map(json.dumps,rows)))
 with pytest.raises(ValueError,match='events mismatch'):m.verify(bad)
