import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_scaled_rotated_bitmap_quad(tmp_path):
    if os.environ.get('VULKAN_TEXT18_AFFINE')!='1':pytest.skip('explicit Vulkan and trusted-font opt in')
    lab=Path(__file__).parent/'fixtures/text_affine_quality_lab/run_lab.py';out=tmp_path/'affine'
    subprocess.run([sys.executable,str(lab),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')],check=True,timeout=240)
    result=json.loads((out/'summary.json').read_text());assert result['status']=='PASS' and len(result['cases'])==4
    spec=importlib.util.spec_from_file_location('affine',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with pytest.raises(ValueError,match='unknown affine case'):m.verify(out,case_name='unregistered')
    bad=tmp_path/'bad';shutil.copytree(out,bad);p=bad/'half/color.rgba32f';b=bytearray(p.read_bytes());b[:4]=b'\0'*4;p.write_bytes(b)
    with pytest.raises(ValueError,match='composition'):m.verify(bad)
