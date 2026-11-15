import os,subprocess,sys,json,importlib.util,shutil
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_COLRV0')!='1',reason='opt-in synthetic COLRv0 Vulkan')
def test_actual_colrv0(tmp_path):
 runner=Path(__file__).parent/'fixtures/text_colrv0_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out)],check=True,capture_output=True,text=True,timeout=180)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and len(s['cases'])==3 and s['palette_count']==3
 spec=importlib.util.spec_from_file_location('colr',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'gpu0',bad);shutil.copyfile(out/'gpu1/color.rgba32f',bad/'color.rgba32f')
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(out,0,bad)
