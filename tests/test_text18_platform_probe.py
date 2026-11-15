"""Actual Linux provider probe; separate from target-platform acceptance."""
import ctypes.util
import json
import os
from pathlib import Path
import pytest
from platform_text_probe import shape

@pytest.fixture
def font():
    p=Path(os.environ.get('TEXT18_TEST_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    if not p.is_file() or not ctypes.util.find_library('harfbuzz'):pytest.skip('explicit local test font/system HarfBuzz unavailable')
    return p

def test_actual_run_and_ligature_mapping(font):
    r=shape(font,'office',language='en')
    assert r['missing_glyphs']==0 and all(g['x_advance']>=0 for g in r['glyphs'])
    assert len(r['glyphs'])<6 and r['upem']>0  # approved DejaVu fixture must shape ligature
    assert r['unit']=='font_units' and r['fallback']=='not_implemented'
    assert all(0<=g['cluster_utf8_byte']<6 for g in r['glyphs'])

def test_actual_combining_normalization(font):
    a=shape(font,'e\u0301');b=shape(font,'é')
    assert a['missing_glyphs']==b['missing_glyphs']==0
    assert [(g['id'],g['x_advance']) for g in a['glyphs']]==[(g['id'],g['x_advance']) for g in b['glyphs']]
    assert a['glyphs'][0]['cluster_utf8_byte']==0

def test_actual_rtl_run(font):
    r=shape(font,'سلام',direction='rtl',language='ar')
    assert r['missing_glyphs']==0
    clusters=[g['cluster_utf8_byte'] for g in r['glyphs']]
    assert clusters==sorted(clusters,reverse=True)
    assert len(clusters)<=4 and sum(g['x_advance'] for g in r['glyphs'])>0

def test_copied_snapshot_survives_provider_cleanup(font):
    r=shape(font,'abc',face_generation=7);before=json.dumps(r,sort_keys=True)
    for _ in range(30):shape(font,'xyz',face_generation=8)
    assert json.dumps(r,sort_keys=True)==before
    assert r['face_generation']==7

def test_invalid_font_rejected(tmp_path):
    p=tmp_path/'bad.ttf';p.write_bytes(b'not a font')
    with pytest.raises(ValueError):shape(p,'abc')

def test_input_budget_before_provider(font):
    with pytest.raises(ValueError):shape(font,'x'*4097)
    with pytest.raises(ValueError):shape(font,'abc',direction='auto')
