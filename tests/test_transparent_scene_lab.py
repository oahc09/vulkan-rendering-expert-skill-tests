"""Artifact verification layer is optional and cannot inherit a historical GPU PASS."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import pytest
LAB=Path(__file__).parent/'fixtures/transparent_scene_lab'

def test_transparent_fixture_sources_and_no_implicit_mobile_claim():
    for name in ['main.cpp','pipeline.hpp','generate.py','PLY_PROFILE.md','run_matrix.py','verify_artifacts.py','build.sh','shaders/lab.vert','shaders/lab.frag','shaders/effects.comp','shaders/resolve.comp']:
        assert (LAB/name).is_file()
    text=(LAB/'README.md').read_text()
    assert 'Explicit unverified scope' in text and 'orthographic' in text and 'Android' in text
    assert 'SOURCE_HASH' not in (LAB/'main.cpp').read_text() # identities are computed from actual sources by the runner

@pytest.mark.host_unit
def test_generated_ply_roundtrip_and_fail_closed():
    spec=importlib.util.spec_from_file_location('transparency_generate',LAB/'generate.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    rows=g.generate(16,.15,115);text=g.encode(rows)
    assert g.decode(text)==rows and len(g.binary(rows))==16*64
    for bad in [text.replace(g.PROFILE,'unknown'),text.replace('property uint set_id','property float set_id'),g.encode(rows+rows[:1]),g.encode([rows[0][:3]+[-1]+rows[0][4:]])]:
        with pytest.raises(ValueError):g.decode(bad)

@pytest.mark.vulkan_integration
def test_actual_transparent_vulkan_artifacts():
    root=os.environ.get('VULKAN_TRAN15_RUN_DIR')
    if not root:pytest.skip('No fresh Transparent Scene Lab run configured; CPU is not GPU evidence')
    subprocess.run([sys.executable,str(LAB/'verify_artifacts.py'),root],check=True,capture_output=True,text=True)
