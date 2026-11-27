import importlib.util,json,os,subprocess,sys
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_vector_scale_lab/run_lab.py'
def module():
 s=importlib.util.spec_from_file_location('scale_lab',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.host_unit
def test_analytic_curve_reference_and_guard():
 m=module()
 assert m.reference(1,32.25,28.25)[0]==1
 assert m.reference(1,32.25,10)[0]==0
 assert m.reference(1,32.25,17.25)[1]
@pytest.mark.vulkan_integration
def test_actual_progressive_curve_mesh(tmp_path):
 if os.environ.get('VULKAN_TEXT18_VECTOR_SCALE')!='1':pytest.skip('opt-in real curve triangle draws')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,capture_output=True,text=True,timeout=240)
 j=json.loads((out/'summary.json').read_text());assert j['draws']==11 and all(r['dense_curve_error']<=.125 for r in j['rows'])
 assert all(r['triangles']==r['vertices']-2 for r in j['rows'])
