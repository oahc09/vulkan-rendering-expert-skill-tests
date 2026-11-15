import importlib.util,json,os,subprocess,sys,shutil
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.skipif(os.environ.get('VULKAN_TEXT18_VECTOR_MESH')!='1',reason='opt-in actual vector triangle draw')
def test_actual_concave_triangle_mesh(tmp_path):
 runner=ROOT/'tests/fixtures/text_vector_mesh_lab/run_lab.py';out=tmp_path/'actual'
 subprocess.run([sys.executable,str(runner),'--out',str(out)],check=True,timeout=180,capture_output=True,text=True)
 s=json.loads((out/'summary.json').read_text());assert s['validation_enabled'] and s['draws']==4 and len(s['rows'])==2
 bad=tmp_path/'bad';shutil.copytree(out/'normal',bad)
 p=bad/'gpu/color.rgba32f';p.write_bytes(b'\0'*len(p.read_bytes()))
 spec=importlib.util.spec_from_file_location('mesh',runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
