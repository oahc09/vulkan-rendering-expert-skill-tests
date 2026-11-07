"""Source checks, fresh artifact acceptance and checker-negative tests are distinct."""
import hashlib,importlib.util,json,os,shutil
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/simulation_lab'

def checker():
    spec=importlib.util.spec_from_file_location('sim16_verify',LAB/'verify_artifacts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def test_simulation_fixture_files_and_scope():
    for name in ('main.cpp','build.sh','build_manifest.py','run_matrix.py','verify_artifacts.py','README.md','shaders/solve.comp','shaders/wave.comp','shaders/bounds.comp'):
        assert (LAB/name).is_file()
    text=(LAB/'README.md').read_text()
    assert 'Explicit unverified scope' in text and '144' in text and '52' in text
    assert 'no degree normalization' in text and 'synchronous fence' in text
    source=(LAB/'shaders/bounds.comp').read_text()
    assert 'barrier()' in source and 'return' not in source
    assert 'atomicAdd' not in ''.join(p.read_text() for p in (LAB/'shaders').glob('*'))

@pytest.mark.vulkan_integration
def test_current_simulation_vulkan_artifacts():
    root=os.environ.get('VULKAN_SIM16_RUN_DIR')
    if not root:pytest.skip('No current clean-source Simulation Lab run; host is not GPU evidence')
    result=checker().verify(root)
    assert result['numerical_cases']==144 and result['draws']==52 and result['shader_artifacts']==15

@pytest.mark.host_unit
def test_verifier_negative_missing_outputs(tmp_path):
    with pytest.raises(OSError):checker().verify(tmp_path)

@pytest.mark.host_unit
def test_verifier_rejects_failure_scope_and_dirty_metadata(tmp_path):
    # Synthetic metadata only: never a simulated GPU pass.
    (tmp_path/'manifest.json').write_text(json.dumps(dict(layer='VulkanIntegration',exit_code=1)))
    (tmp_path/'result.json').write_text('{}')
    with pytest.raises(ValueError,match='execution failed'):checker().verify(tmp_path)
    (tmp_path/'manifest.json').write_text(json.dumps(dict(layer='VulkanIntegration',exit_code=0,tests_dirty=True,skill_dirty=False)))
    with pytest.raises(ValueError,match='dirty source'):checker().verify(tmp_path)
