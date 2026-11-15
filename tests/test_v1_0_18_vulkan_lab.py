"""Opt-in real Vulkan execution. Missing opt-in is SKIP, never GPU PASS."""
import os,subprocess,sys,json
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration

def test_actual_text_coverage_upload_and_preserved_overlay(tmp_path):
    if os.environ.get('VULKAN_TEXT18_LAB')!='1':pytest.skip('set VULKAN_TEXT18_LAB=1 with compiler, headers and authorized ICD')
    lab=Path(__file__).parent/'fixtures/text_vector_lab/run_lab.py'
    out=tmp_path/'actual-vulkan'
    subprocess.run([sys.executable,str(lab),'--out',str(out)],check=True)
    report=json.loads((out/'summary.json').read_text())
    assert report['status']=='PASS' and report['layer']=='actual Vulkan integration'
    assert len(json.loads((out/'pixel-verification.json').read_text()))==5
    # A corrupted readback must fail independently of the C++ PASS text.
    import importlib.util, shutil
    spec=importlib.util.spec_from_file_location('text18_lab_verifier',lab)
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    altered=tmp_path/'tampered';shutil.copytree(out,altered)
    victim=altered/'frames/frame-1.id32f';data=bytearray(victim.read_bytes());data[:4]=b'\0'*4;victim.write_bytes(data)
    with pytest.raises(ValueError,match='sentinel'):verifier.verify(altered)
