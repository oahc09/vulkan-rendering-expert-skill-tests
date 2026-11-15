import json,os,subprocess,sys
from pathlib import Path
import pytest
pytestmark=pytest.mark.vulkan_integration
def test_actual_refined_multilingual_board(tmp_path):
 if os.environ.get('TEXT18_SCENE_A_REFINED')!='1':pytest.skip('explicit real multilingual representation board opt-in')
 font=os.environ.get('TEXT18_VARIABLE_FONT');source=os.environ.get('TEXT18_MSDF_SOURCE')
 if not font or not source:pytest.fail('TEXT18_VARIABLE_FONT and TEXT18_MSDF_SOURCE required')
 out=tmp_path/'actual'
 subprocess.run([sys.executable,str(Path(__file__).parent/'fixtures/scene_a_refined_board_lab/run_lab.py'),'--out',str(out),'--variable-font',font,'--msdf-source',source],check=True,timeout=600)
 r=json.loads((out/'summary.json').read_text())
 assert r['status']=='SAMPLING_PASS_QUALITY_NOT_QUALIFIED' and r['rows']==7
 assert not r['failed_sampling_cases'] and all(m['excluded_pixels']==0 for m in r['metrics'])
 assert {m['row'] for m in r['metrics']}=={'chinese','ligature','combining','bidi','emoji','variable-light','variable-heavy'}
 assert r['negative_errors']['double-alpha']>1e-6 and r['negative_errors']['wrong-range']>.004

 assert r['msdf_density']==4 and r['output_size']==[65,65]
 assert len([m for m in r['metrics'] if m['transform']=='square-rotate90'])==13
