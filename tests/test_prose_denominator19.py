import copy,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import prose_denominator19 as r
pytestmark=pytest.mark.candidate19
def files():
 def f(raw):return {'mode':'100644','kind':'blob','blob':'synthetic','raw':raw}
 return {'a.adoc':f(b'ifdef::A[]\nifdef::B[inline body]\ninclude::b.adoc[tag=part]\ninclude::{generated}/x.adoc[]\n:unknown: value\nendif::A[]\n'),'b.adoc':f(b'include::b.adoc[tag=part]\n'),'new.unknown':f(b'keep'),'Makefile':f(b'all: generated\n\tpython gen.py\n')}
def test_positive_inline_nested_and_tag():
 f=files();v=r.build(f);assert r.verify(v,f);g=v['adoc_graph'];edge=next(x for x in g if x.get('line')==3 and x['source']=='a.adoc')
 assert len(edge['outer_conditions'])==1 and edge['options_raw']=='[tag=part]'
 assert edge['resolution']=='TRACKED_LITERAL_TARGET_ONLY'
 assert v['tracked_sources']['new.unknown']['category']=='OTHER_UNCLASSIFIED_RETAINED'
 assert v['closure_status']=='BLOCKED'
 assert any(x.get('resolution')=='UNRESOLVED_GENERATED_MACRO_OR_MISSING' for x in g)
@pytest.mark.parametrize('kind',['file','condition','edge','resolution','closure','generation','duplicate'])
def test_mutants(kind):
 f=files();v=r.build(f);assert r.verify(v,f)
 if kind=='file':v['tracked_sources'].pop('new.unknown')
 elif kind=='condition':v['adoc_graph'][0]['raw']='changed'
 elif kind=='edge':v['adoc_graph'].pop()
 elif kind=='resolution':v['adoc_graph'][2]['resolution']='EXPANDED'
 elif kind=='closure':v['closure_status']='COMPLETE'
 elif kind=='generation':v['generation_references']=[]
 else:v['adoc_graph'].append(copy.deepcopy(v['adoc_graph'][0]))
 with pytest.raises(ValueError):r.verify(v,f)
def test_existing_semantic_controls():
 b=r.semantic_bridge(Path(__file__).resolve().parents[1]);assert b['results']['required_missing']['vuids']==['VUID-vkBindBufferMemory-buffer-01444']
def test_fixed_source_optional():
 p=Path('/workspace/scratch/62d43a81bbde/cts-src/external/vulkan-docs/src')
 if not p.is_dir():pytest.skip('fixed source unavailable, not executed')
 f=r.load(p);v=r.build(f);assert r.verify(v,f);assert len(f)==1340
 span=next(x for x in v['manual_span_candidates'] if x.get('refpage')=='VkMemoryDedicatedRequirements')
 assert any('VK_KHR_dedicated_allocation' in c['directive'] for c in span['outer_conditions'])
 assert span['generated_includes']

def test_blob_bytes_not_oid_claim():
 import hashlib
 raw=b'original';oid=hashlib.sha1(b'blob 8\0'+raw).hexdigest()
 assert r.validate_blob(raw,oid,8)==raw
 with pytest.raises(ValueError):r.validate_blob(b'modified',oid,8)
 with pytest.raises(ValueError):r.validate_blob(raw,oid,7)
