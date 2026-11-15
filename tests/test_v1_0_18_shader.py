"""Actual optional shader compiler gate; skips are not successful compilation."""
from pathlib import Path
import shutil,subprocess
import pytest
pytestmark=pytest.mark.shader_unit

def test_coverage_glsl_compiles_and_validates(tmp_path):
    glslang=shutil.which('glslangValidator');validator=shutil.which('spirv-val')
    if not glslang or not validator: pytest.skip('glslangValidator / spirv-val unavailable; NOT_RUN')
    source=Path(__file__).parent/'fixtures/text_vector_lab/coverage.frag'
    binary=tmp_path/'coverage.spv'
    subprocess.run([glslang,'-V','--target-env','vulkan1.1',str(source),'-o',str(binary)],check=True,capture_output=True)
    subprocess.run([validator,'--target-env','vulkan1.1',str(binary)],check=True,capture_output=True)
    assert binary.read_bytes()[:4]==b'\x03\x02\x23\x07'
