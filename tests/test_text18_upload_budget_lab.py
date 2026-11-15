import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
LAB=Path(__file__).parent/'fixtures/text_upload_budget_lab/run_lab.py'
def test_actual_upload_budget_backpressure(tmp_path):
 if os.environ.get('VULKAN_TEXT18_UPLOAD_BUDGET')!='1':pytest.skip('explicit Vulkan opt-in')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(LAB),'--out',str(out)],check=True,timeout=300)
 r=json.loads((out/'summary.json').read_text());assert r['validation_enabled'] and r['cycles']==3 and len(r['rows'])==6
 s=importlib.util.spec_from_file_location('budget_lab',LAB);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 bad=tmp_path/'bad';shutil.copytree(out/'frames',bad/'frames');events=[json.loads(x) for x in (bad/'frames/events.jsonl').read_text().splitlines()]
 for e in events:
  if e['kind']=='cancel_pending':e['state']['inflight_bytes']=0;break
 (bad/'frames/events.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
 with pytest.raises(ValueError,match='cancel pending accounting'):m.verify(bad)
 bad2=tmp_path/'bad2';shutil.copytree(out/'frames',bad2/'frames');shutil.copytree(out/'reference-full',bad2/'reference-full');shutil.copytree(out/'reference-half',bad2/'reference-half');shutil.copyfile(out/'frames/old-0/color.rgba32f',bad2/'frames/new-0/color.rgba32f')
 with pytest.raises(ValueError,match='composition mismatch'):m.verify(bad2)
