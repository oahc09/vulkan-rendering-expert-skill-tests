import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_packed_uv_glyph_quads(tmp_path):
    if os.environ.get('VULKAN_TEXT18_PACKED_QUAD')!='1':pytest.skip('trusted font plus explicit Vulkan toolchain opt-in')
    lab=Path(__file__).parent/'fixtures/text_packed_quad_lab/run_lab.py';out=tmp_path/'actual'
    subprocess.run([sys.executable,str(lab),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')],check=True,timeout=180)
    result=json.loads((out/'summary.json').read_text());assert result['status']=='PASS' and result['numeric']['vertices']==18 and result['numeric']['clipped_nonzero_source_pixels']>0
    spec=importlib.util.spec_from_file_location('quad',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    bad=tmp_path/'bad';shutil.copytree(out,bad)
    p=bad/'gpu/color.rgba32f';b=bytearray(p.read_bytes());b[:4]=b'\0'*4;p.write_bytes(b)
    with pytest.raises(ValueError,match='composition'):m.verify(bad)
    overlapping=tmp_path/'overlap';shutil.copytree(out,overlapping)
    p=overlapping/'reference.json';r=json.loads(p.read_text());r['glyphs'][1]['destination']=r['glyphs'][0]['destination'];p.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='overlapping'):m.verify(overlapping)
