"""Opt-in real timeline-counter experiment, never CPU-only GPU evidence."""
import importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_multiple_pending_consumers_retire_before_slot_reuse(tmp_path):
    if os.environ.get('VULKAN_TEXT18_INFLIGHT')!='1':pytest.skip('set VULKAN_TEXT18_INFLIGHT=1 with authorized software/device ICD and Vulkan headers')
    runner=Path(__file__).parent/'fixtures/text_inflight_lab/run_lab.py'
    out=tmp_path/'inflight'
    subprocess.run([sys.executable,str(runner),'--out',str(out)],check=True,timeout=180)
    report=json.loads((out/'summary.json').read_text())
    assert report['status']=='PASS'
    assert report['numeric']['consumer_count']==3
    spec=importlib.util.spec_from_file_location('text18_inflight_verify',runner)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    altered=tmp_path/'tampered';shutil.copytree(out,altered)
    p=altered/'frames/retirement.jsonl';rows=[json.loads(s) for s in p.read_text().splitlines()];rows[1]['reuse_allowed']=True;p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
    with pytest.raises(ValueError,match='retirement boundary'):module.verify(altered)
    shutil.rmtree(altered);shutil.copytree(out,altered)
    shutil.copyfile(altered/'frames/consumer-0.r32f',altered/'frames/consumer-2.r32f')
    with pytest.raises(ValueError,match='wrong generation'):module.verify(altered)
