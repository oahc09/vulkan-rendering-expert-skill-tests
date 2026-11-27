import importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_phase_sequence_lab/run_lab.py'
def module():
 s=importlib.util.spec_from_file_location('phase_sequence',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.host_unit
def test_phase_branches_same_transform_distinct_history():
 m=module();r=m.trace();assert len(r)==37
 assert [x['selected'] for x in r if x['kind']=='measured']==[0]*17+[1]*17
 assert m.PHASES[0]==0 and m.PHASES[-1]==1 and len(m.PHASES)==17
 assert r[-1]==dict(kind='negative',branch=0,frame=8,expected=0,actual=1)
@pytest.mark.host_unit
def test_phase_statistics_use_foreground_and_edges_not_background():
 m=module();a=[0.]*(m.m.W*m.m.H);b=a.copy();a[5]=.6;b[5]=.5
 r=m.stats(a,b);assert r['foreground_mae']==pytest.approx(.1) and r['edge_mae']==pytest.approx(.1)
 assert r['foreground_pixels']==1 and r['worst_xy']==[5,0]
@pytest.mark.vulkan_integration
def test_actual_phase_sequence_persistent_evidence():
 if os.environ.get('VULKAN_TEXT18_PHASE_SEQUENCE')!='1':pytest.skip('explicit trusted phase sequence opt-in')
 source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not source:pytest.fail('TEXT18_MSDF_SOURCE required')
 root=Path(os.environ.get('TEXT18_PHASE_OUTPUT_ROOT','/tmp/text18-phase-sequence-evidence'));root.mkdir(parents=True,exist_ok=True)
 out=Path(tempfile.mkdtemp(prefix='run-',dir=root))/'experiment'
 subprocess.run([sys.executable,str(LAB),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--msdf-source',source],check=True,timeout=360)
 r=json.loads((out/'summary.json').read_text());assert r['status']=='MEASURED_NOT_QUALIFIED'
 assert len(r['frames'])==34 and len(r['warmup'])==2 and len(r['temporal_geometry_subtracted_residual'])==32
 assert r['negative_wrong_hold_rgba_error']>1e-6
 print('Persistent evidence:',out)
