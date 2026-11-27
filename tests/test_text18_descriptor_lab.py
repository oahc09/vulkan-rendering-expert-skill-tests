import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_pending_descriptor_draw_retirement(tmp_path):
    if os.environ.get('VULKAN_TEXT18_DESCRIPTOR')!='1':pytest.skip('explicit opt in and Vulkan toolchain/validation required')
    lab=Path(__file__).parent/'fixtures/text_descriptor_lab/run_lab.py';out=tmp_path/'run'
    subprocess.run([sys.executable,str(lab),'--out',str(out)],check=True,timeout=180)
    assert json.loads((out/'summary.json').read_text())['status']=='PASS'
    spec=importlib.util.spec_from_file_location('descriptor_lab',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    bad=tmp_path/'bad';shutil.copytree(out,bad)
    (bad/'frames/generation-1/color.rgba32f').write_bytes((bad/'frames/generation-0/color.rgba32f').read_bytes())
    with pytest.raises(ValueError,match='descriptor'):m.verify(bad)
    bad2=tmp_path/'event';shutil.copytree(out,bad2)
    p=bad2/'vulkan.log';p.write_text(p.read_text().replace('"pending_fence_not_ready":true','"pending_fence_not_ready":false'))
    with pytest.raises(ValueError,match='retirement'):m.verify(bad2)
