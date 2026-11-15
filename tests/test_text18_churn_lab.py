import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_64_generation_retirement(tmp_path):
    if os.environ.get('VULKAN_TEXT18_CHURN')!='1':pytest.skip('opt-in explicit Vulkan toolchain/ICD required')
    lab=Path(__file__).parent/'fixtures/text_churn_lab/run_lab.py';out=tmp_path/'run'
    subprocess.run([sys.executable,str(lab),'--out',str(out)],check=True,timeout=180)
    assert json.loads((out/'summary.json').read_text())['status']=='PASS'
    s=importlib.util.spec_from_file_location('churn',lab);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    bad=tmp_path/'bad';shutil.copytree(out,bad)
    p=bad/'frames/g63-c1.f32';p.write_bytes((bad/'frames/g62-c1.f32').read_bytes())
    with pytest.raises(ValueError,match='generation'):m.verify(bad)
    bad2=tmp_path/'bad-event';shutil.copytree(out,bad2)
    p=bad2/'frames/generations.jsonl';rows=p.read_text().splitlines();r=json.loads(rows[31]);r['reuse_before_B']=True;rows[31]=json.dumps(r);p.write_text('\n'.join(rows))
    with pytest.raises(ValueError,match='boundary'):m.verify(bad2)
