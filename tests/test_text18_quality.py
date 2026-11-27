import importlib.util,os,sys,subprocess,json
from pathlib import Path
import pytest
LAB=Path(__file__).parent/'fixtures/text_bitmap_lab'
spec=importlib.util.spec_from_file_location('text_quality',LAB/'quality_cases.py');quality=importlib.util.module_from_spec(spec);spec.loader.exec_module(quality)

@pytest.mark.host_unit
def test_translation_oracle_rejects_stuck_and_area_drift():
    base=[0.]*(65*49)
    for y in range(10,20):
        for x in range(10,20):base[y*65+x]=1.
    with pytest.raises(ValueError,match='centroid'):quality.verify_translation([base]*4)
    with pytest.raises(ValueError,match='area'):quality.verify_translation([base,[x*.5 for x in base],base,base])

@pytest.mark.vulkan_integration
def test_actual_subpixel_font_sequence(tmp_path):
    if os.environ.get('VULKAN_TEXT18_BITMAP')!='1':pytest.skip('trusted font and explicit Vulkan opt-in required')
    out=tmp_path/'quality'
    subprocess.run([sys.executable,str(LAB/'run_lab.py'),'--quality','--font',os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),'--out',str(out)],check=True,timeout=240)
    report=json.loads((out/'summary.json').read_text())['quality']
    assert len(report['cases'])==8 and all(r['validation_enabled'] for r in report['cases'])
