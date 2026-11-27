import os,sys,subprocess,json,importlib.util,shutil
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_EXTRUSION')!='1',reason='opt-in real finite extrusion Vulkan')
def test_actual_extrusion(tmp_path):
 runner=Path(__file__).parent/'fixtures/text_extrusion_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out)],check=True,capture_output=True,text=True,timeout=180)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and len(s['cases'])==2
 assert all(r['surface_pixels']['side']>0 and r['surface_pixels']['front']>0 for r in s['cases'])
 spec=importlib.util.spec_from_file_location('extrusion',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'normal',bad);p=bad/'depth.f32';p.write_bytes(bytes(p.stat().st_size))
 with pytest.raises(ValueError,match='color/depth mismatch'):m.verify(bad)
