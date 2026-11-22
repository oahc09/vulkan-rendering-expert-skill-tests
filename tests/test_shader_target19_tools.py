"""Actually rerun the offline three-tool experiment when installed; never device evidence."""
import json,shutil,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.shader_unit

def test_actual_offline_shader_target_pair(tmp_path):
 paths=[shutil.which(n) for n in ('glslangValidator','spirv-val','spirv-dis')]
 if not all(paths):pytest.skip('offline shader tools unavailable; NOT_RUN')
 dirs={str(Path(p).parent) for p in paths}
 if len(dirs)!=1:pytest.skip('runner requires colocated tools; NOT_RUN')
 runner=Path(__file__).parents[1]/'cases19/shader_target/run.py'
 out=tmp_path/'offline'
 subprocess.run([sys.executable,'-O',str(runner),'--tools',dirs.pop(),'--output',str(out)],check=True,timeout=120)
 d=json.loads((out/'summary.json').read_text())
 assert d['status']=='OFFLINE_TARGET_CAPABILITY_PAIR_PASS'
 assert d['cases']['float64_11']['extraction']['capabilities']==['Shader','Float64']
 c=d['cases']['base12']
 assert c['validate']['exit_code']==0 and c['wrong_target']['exit_code']!=0
 assert c['validate']['artifact_sha256']==c['wrong_target']['artifact_sha256']==c['spirv_sha256']
