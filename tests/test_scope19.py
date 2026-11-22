import importlib.util,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from scope19 import dependencies,evaluate,collect
pytestmark=pytest.mark.host_unit
@pytest.mark.parametrize('text,values,expected',[
 ('A+B,C',{'A':True,'B':False,'C':True},True),
 ('A+(B,C)',{'A':True,'C':False},None),
 ('A+(B,C)',{'A':False},False),
 ('(A,B)+(C,D)',{'A':True,'D':True},True),
 ('',{},True),('A',{},None)])
def test_dependencies(text,values,expected):assert evaluate(dependencies(text),values) is expected
@pytest.mark.parametrize('text',['A|B','A+',',A','(A','A B','A)','A++B'])
def test_invalid(text):
    with pytest.raises(ValueError):dependencies(text)
def test_members_and_variant_distinct():
    raw=b'<registry><types><type category="struct" name="X" structextends="Y"><member optional="true"><type>T</type><name>p</name></member></type></types><commands/><feature api="vulkansc" number="1.0" name="SC"/><extensions/></registry>'
    x=collect(raw);assert x['types'][0]['members'][0]['attributes']['optional']=='true'
    assert x['sc_variant_records'][0]['name']=='SC'
    assert x['claims']['semantic_L1_L2']=='UNREVIEWED'

def test_member_dependency():
    assert evaluate(dependencies('VK_A+VkFeatures::field'),{'VK_A':True,'VkFeatures::field':True}) is True
    assert evaluate(dependencies('VkFeatures::field'),{'VkFeatures':True}) is None
