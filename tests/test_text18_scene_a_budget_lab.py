import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_compact_budget_perspective_board(tmp_path):
 if os.environ.get('TEXT18_SCENE_A_BUDGET')!='1':pytest.skip('explicit compact budget perspective board opt-in')
 required=['TEXT18_VARIABLE_FONT','TEXT18_MSDF_SOURCE','TEXT18_REFINED_BOARD_SOURCE']
 if any(not os.environ.get(k) for k in required):pytest.fail('required trusted source/font/renderer paths not supplied')
 out=tmp_path/'actual';subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/scene_a_budget_board_lab/run_lab.py'),'--out',str(out),'--source',os.environ[required[2]],'--variable-font',os.environ[required[0]],'--msdf-source',os.environ[required[1]]],check=True,timeout=600)
 s=json.loads((out/'summary.json').read_text());assert s['status']=='SAMPLING_PASS_QUALITY_NOT_QUALIFIED' and s['validation_enabled']
 assert len(s['metrics'])==86 and len(s['plans'])==14 and s['rejected_before_gpu']==7
 assert len(s['metadata_negative_errors'])==2 and all(x>.004 for x in s['metadata_negative_errors'])
 low=[p for p in s['plans'] if p['budget']==200000];assert sum(p['mode']==0 for p in low)==4 and sum(p['mode']==1 for p in low)==2
 assert all(m['max_composition_error']<=m['tolerance'] and m['excluded_pixels']==0 for m in s['metrics'])
