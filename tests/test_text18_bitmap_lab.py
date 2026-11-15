"""Opt-in actual Linux font bitmap/Vulkan bridge, not mobile typography acceptance."""
import os,sys,subprocess,json,importlib.util,shutil
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_shaped_glyph_bitmap_composition(tmp_path):
    if os.environ.get('VULKAN_TEXT18_BITMAP')!='1':pytest.skip('opt in with trusted font, freetype-py and Vulkan toolchain')
    lab=Path(__file__).parent/'fixtures/text_bitmap_lab/run_lab.py';out=tmp_path/'actual'
    font=os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    subprocess.run([sys.executable,str(lab),'--out',str(out),'--font',font],check=True,timeout=240)
    r=json.loads((out/'summary.json').read_text());assert r['status']=='PASS' and len(r['cases'])==3 and len(r['vector_cases'])==5
    assert all(row['validation_enabled'] for row in r['cases']+r['vector_cases'])
    spec=importlib.util.spec_from_file_location('bitmap_lab',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    bad=tmp_path/'bad';shutil.copytree(out/'ffi',bad)
    p=bad/'gpu/color.rgba32f';data=bytearray(p.read_bytes());data[:4]=b'\0'*4;p.write_bytes(data)
    with pytest.raises(ValueError,match='composition'):m.verify(bad)
    bad2=tmp_path/'sentinel';shutil.copytree(out/'O',bad2)
    p=bad2/'gpu/id.rgba32f';data=bytearray(p.read_bytes());data[:4]=b'\0'*4;p.write_bytes(data)
    with pytest.raises(ValueError,match='sentinel'):m.verify(bad2)
