import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_handoff_lab/run_lab.py'
def test_actual_pre_overlay_post_handoff(tmp_path):
 if os.environ.get('VULKAN_TEXT18_HANDOFF')!='1':pytest.skip('explicit Vulkan handoff opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=240)
 summary=json.loads((out/'summary.json').read_text());assert summary['validation_enabled'] and summary['positive_draws']==3
 assert len(summary['negatives'])==6 and all(r['changed_pixels']>0 for r in summary['negatives'])
 spec=importlib.util.spec_from_file_location('handoff',LAB);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'normal',bad);(bad/'color.f32').write_bytes((out/'pipeline/color.f32').read_bytes())
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad)
