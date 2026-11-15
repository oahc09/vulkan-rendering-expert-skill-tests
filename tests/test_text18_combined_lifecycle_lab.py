import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_combined_packed_draw_lifecycle(tmp_path):
    if os.environ.get('VULKAN_TEXT18_COMBINED')!='1':pytest.skip('explicit Vulkan and trusted-font opt-in')
    lab=Path(__file__).parent/'fixtures/text_combined_lifecycle_lab/run_lab.py';out=tmp_path/'actual'
    subprocess.run([sys.executable,str(lab),'--out',str(out),'--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')],check=True,timeout=240)
    assert json.loads((out/'summary.json').read_text())['status']=='PASS'
    spec=importlib.util.spec_from_file_location('combined',lab);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    bad=tmp_path/'bad-generation';shutil.copytree(out,bad)
    (bad/'frames/new-B/color.rgba32f').write_bytes((bad/'frames/old-A/color.rgba32f').read_bytes())
    with pytest.raises(ValueError,match='composition'):m.verify(bad)
    bad2=tmp_path/'bad-events';shutil.copytree(out,bad2)
    p=bad2/'frames/events.jsonl';rows=p.read_text().splitlines();r=json.loads(rows[0]);r['published']=1;rows[0]=json.dumps(r);p.write_text('\n'.join(rows))
    with pytest.raises(ValueError,match='events'):m.verify(bad2)
