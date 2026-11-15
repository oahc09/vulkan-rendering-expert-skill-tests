import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_active_mrt_and_depth_preservation(tmp_path):
    if os.environ.get('VULKAN_TEXT18_ACTIVE_MRT')!='1':pytest.skip('explicit Vulkan toolchain opt in')
    lab=Path(__file__).parent/'fixtures/text_active_mrt_lab/run_lab.py';out=tmp_path/'actual'
    subprocess.run([sys.executable,str(lab),'--out',str(out)],check=True,timeout=180)
    r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and r['active_color_attachments']==3 and r['validation_enabled']
    s=importlib.util.spec_from_file_location('active',lab);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    bad=tmp_path/'bad';shutil.copytree(out/'normal',bad);p=bad/'depth.f32';v=bytearray(p.read_bytes());v[:4]=b'\0'*4;p.write_bytes(v)
    with pytest.raises(ValueError,match='depth'):m.verify(bad)
