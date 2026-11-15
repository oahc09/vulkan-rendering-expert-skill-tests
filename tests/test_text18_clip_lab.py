import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_nested_fragment_clips(tmp_path):
    if os.environ.get('VULKAN_TEXT18_CLIP')!='1':pytest.skip('explicit Vulkan toolchain and validation opt-in')
    lab=Path(__file__).parent/'fixtures/text_clip_lab/run_lab.py';out=tmp_path/'clips'
    subprocess.run([sys.executable,str(lab),'--out',str(out)],check=True,timeout=180)
    result=json.loads((out/'summary.json').read_text());assert result['status']=='PASS' and result['draws']==4
    spec=importlib.util.spec_from_file_location('clip_lab',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    # Bounding rectangle alone is not an exact rotated/curved clip.
    assert not m.predicate(12.5,10.5) and m.predicate(30.5,25.5)
    bad=tmp_path/'bad';shutil.copytree(out/'correct',bad)
    p=bad/'gpu/color.rgba32f';b=bytearray(p.read_bytes());b[:4]=b'\0'*4;p.write_bytes(b)
    with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
