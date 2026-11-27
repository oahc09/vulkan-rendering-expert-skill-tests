"""MSDF CPU reference checks plus explicitly enabled real Vulkan experiment."""
import importlib.util,json,os,subprocess,sys,shutil
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_msdf_lab/run_lab.py'

def module():
 spec=importlib.util.spec_from_file_location('text18_msdf',LAB);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.mark.host_unit
def test_independent_outline_reference_keeps_hole():
 m=module()
 def rectangle(x0,y0,x1,y1):return [[(x0,y0),(x1,y0)],[(x1,y0),(x1,y1)],[(x1,y1),(x0,y1)],[(x0,y1),(x0,y0)]]
 cov=m.geometry_coverage([rectangle(10,10,30,30),rectangle(15,15,25,25)],1,0)
 assert cov[12*m.W+12]==1 and cov[20*m.W+20]==0
 assert sum(cov)==300

@pytest.mark.host_unit
def test_true_rgb_median_not_single_channel():
 m=module();atlas=[.1,.7,.8,1.]*(m.W*m.H)
 assert m.reconstructed(atlas,1,0)[0]==pytest.approx(1.)
 atlas=[.1,.1,.1,1.]*(m.W*m.H)
 assert m.reconstructed(atlas,1,0)[0]==0

@pytest.mark.vulkan_integration
def test_actual_edge_colored_msdf_gpu_and_outline_gate(tmp_path):
 if os.environ.get('VULKAN_TEXT18_MSDF')!='1':pytest.skip('explicit trusted font and local msdfgen/Vulkan opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE must identify a pinned local checkout')
 out=tmp_path/'msdf'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=360)
 result=json.loads((out/'summary.json').read_text())
 assert result['status']=='PASS' and len(result['cases'])==8
 assert set(result['negatives'])=={'wrong-channel','wrong-srgb','wrong-range'}
 m=module();folder=out/'A/native';atlas=m.floats(out/'A/atlas.rgba32f',m.W*m.H*4);contours=json.loads((out/'A/outline.json').read_text())
 negative=out/'tampered-negative';shutil.copytree(folder,negative)
 p=negative/'color.rgba32f';data=bytearray(p.read_bytes());data[:4]=b'\0'*4;p.write_bytes(data)
 with pytest.raises(ValueError,match='sampling/composition'):m.verify_case(negative,atlas,contours,1,0)

@pytest.mark.host_unit
def test_outline_clipping_and_padding_rejected():
 m=module()
 with pytest.raises(ValueError,match='clipping/padding'):m.check_bounds([[[(-1,3),(4,4)]]])
 with pytest.raises(ValueError,match='clipping/padding'):m.check_bounds([[[ (2,3),(4,4)]]],margin=3.)
 m.check_bounds([[[ (10,10),(20,20)]]],margin=3.)
