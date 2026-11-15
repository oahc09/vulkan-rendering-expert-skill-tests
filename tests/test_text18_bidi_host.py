import importlib.util
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
HERE=Path(__file__).parent/'fixtures/text_bidi_lab'
def load(n):
 s=importlib.util.spec_from_file_location(n,HERE/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.parametrize('text,base',[('',0),('x'*65,0),('\U0001f600',0),('a\u2067b',0),('a\nb',0),('x',2)])
def test_pre_provider_bounded_input(text,base):
 m=load('bidi')
 for fn in (m.resolve,m.icu):
  with pytest.raises(ValueError,match='bounded BMP paragraph input'):fn(text,base)
def test_only_audited_paragraph():
 with pytest.raises(ValueError,match='only fixed audited paragraph supported'):load('bidi').runs('other',0)
def test_independent_reference_ignores_candidate_destinations():
 m=load('run_lab');items=[]
 for start,advance in [(0,4),(1,8)]:items.append({'source':{'start':start,'end':start+1},'destination':[999,999],'crop_offset':[1,-3],'advance':999,'shape':{'upem':1000,'glyphs':[{'x_advance':advance*100}]}})
 result=m.reference_from_icu(items,{'levels':[1,2],'visual_to_logical':[1,0]},16)
 assert [g['destination'] for g in result]==[[4,13],[12,13]]
