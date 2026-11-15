import importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_phase_integration_lab/run_lab.py'
def module():
 s=importlib.util.spec_from_file_location('higher_grid',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.host_unit
def test_constant_atlas_and_grid_contract():
 m=module()
 for n in (4,8,16):
  assert set(m.sampled([1.]*(65*49*4),m.b.SCALE,.125,n))=={1.}
  assert set(m.sampled([0.]*(65*49*4),m.b.SCALE,.125,n))=={0.}
 with pytest.raises(ValueError,match='grid'):m.sampled([],1,0,3)
@pytest.mark.vulkan_integration
def test_actual_higher_grid_phase_evidence():
 if os.environ.get('VULKAN_TEXT18_PHASE_INTEGRATION')!='1':pytest.skip('explicit trusted GPU opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE required')
 root=Path('/tmp/text18-phase-integration-evidence');root.mkdir(exist_ok=True)
 out=Path(tempfile.mkdtemp(prefix='run-',dir=root))/'experiment'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=600)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='MEASURED_NOT_QUALIFIED'
 for mode in ('linear4','linear8','linear16'):
  v=r['modes'][mode];assert len(v['frames'])==34 and len(v['warmup'])==2 and len(v['temporal_geometry_subtracted_residual'])==32
  assert v['negative_wrong_hold_rgba_error']>1e-6
 print('Persistent evidence:',out)
