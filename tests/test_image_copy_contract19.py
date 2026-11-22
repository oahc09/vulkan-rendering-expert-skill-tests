import copy
import pytest
from tools import image_copy_contract19 as m

def fmt(block,bytes_,compressed):return dict(color=True,single_plane=True,alpha_only_format=False,supported=True,compressed=compressed,block_extent=block,block_bytes=bytes_)
BC1=fmt([4,4,1],8,True)
RG32=fmt([1,1,1],8,False)
RGBA8=fmt([1,1,1],4,False)

@pytest.mark.parametrize('a,b',[(BC1,RG32),(RG32,BC1),(BC1,BC1),(RG32,RG32)])
def test_admitted_format(a,b):assert m.format_admit(a,b)['status']=='FORMAT_CONDITIONS_WITHIN_SCOPE'

def test_size_not_compatible():assert m.format_admit(BC1,RGBA8)['vuids']==['VUID-vkCmdCopyImage-srcImage-01548']

def test_both_compressed_extent():
    a=fmt([4,4,1],16,True);b=fmt([8,5,1],16,True)
    assert m.format_admit(a,b)['vuids']==['VUID-vkCmdCopyImage-srcImage-09247']
    assert m.representation_blocks_equal([4,4,1],[8,5,1],a['block_extent'],b['block_extent'])['status']=='BLOCK_COUNTS_EQUAL'

@pytest.mark.parametrize('extent',[[5,1,1],[6,1,1],[7,1,1],[8,1,1]])
def test_ceil_not_unique_destination(extent):
    r=m.representation_blocks_equal([2,1,1],extent,[1,1,1],[4,4,1])
    assert r['status']=='BLOCK_COUNTS_EQUAL' and r['unique_destination_extent_inferred'] is False

def test_astc_example():assert m.representation_blocks_equal([7,3,1],[1,1,1],[8,5,1],[1,1,1])['status']=='BLOCK_COUNTS_EQUAL'

def test_not_equal():assert m.representation_blocks_equal([7,4,1],[1,1,1],[4,4,1],[1,1,1])['status']=='BLOCK_COUNTS_DIFFER'

@pytest.mark.parametrize('side',['src','dst'])
def test_partial_edge_extent_allowed(side):
    r=m.image_region(BC1,[4,0,0],[3,4,1],[7,4,1],side)
    assert r['status']=='LOCAL_REGION_CONDITIONS_WITHIN_SCOPE' and r['complete_copy_admission'] is False

@pytest.mark.parametrize('side,vuid',[('src','07278'),('dst','07281')])
def test_offset_no_edge_exception(side,vuid):
    r=m.image_region(BC1,[3,0,0],[4,4,1],[7,4,1],side)
    assert r['status']=='REJECTED' and r['vuids']==[f'VUID-vkCmdCopyImage-pRegions-{vuid}']

@pytest.mark.parametrize('side,vuid',[('src','01728'),('dst','01732')])
def test_nonedge_partial_rejected(side,vuid):assert m.image_region(BC1,[0,0,0],[3,4,1],[7,4,1],side)['vuids']==[f'VUID-vkCmdCopyImage-{side}Image-{vuid}']

def test_bounds_separate():
    r=m.image_region(BC1,[4,0,0],[8,4,1],[7,4,1],'src')
    assert r['status']=='REJECTED' and r['out_of_bounds_axes']==[0]

def test_uncompressed_no_block_alignment():assert m.image_region(RG32,[1,1,0],[1,1,1],[3,3,1],'dst')['status']=='LOCAL_REGION_CONDITIONS_WITHIN_SCOPE'

@pytest.mark.parametrize('field,value',[('alpha_only_format',True),('color',False),('single_plane',False),('supported',False),('compressed',1),('block_bytes',True),('block_bytes',0),('block_extent',[4,False,1])])
def test_unknown_metadata(field,value):
    a=copy.deepcopy(BC1);a[field]=value
    assert m.format_admit(a,RG32)['status']=='UNKNOWN'

@pytest.mark.parametrize('bad',[None,[],{},True])
def test_unknown_shape(bad):assert m.format_admit(bad,RG32)['status']=='UNKNOWN'

@pytest.mark.parametrize('offset,extent',[([True,0,0],[4,4,1]),([2**31,0,0],[4,4,1]),([0,0,0],[0,4,1]),([0,0,0],[2**32,4,1]),([0,0,0],[4,4])])
def test_unknown_region(offset,extent):assert m.image_region(BC1,offset,extent,[7,4,1],'src')['status']=='UNKNOWN'

def test_negative_offset_bounds():assert m.image_region(BC1,[-4,0,0],[4,4,1],[7,4,1],'src')['status']=='REJECTED'

def test_extra_metadata_rejected():
    a=copy.deepcopy(BC1);a['pNext']='special'
    assert m.format_admit(a,RG32)['status']=='UNKNOWN'

def test_rgba_alpha_channel_is_not_alpha_only_format():
    # Ordinary RGBA8 has an alpha channel, but is not the A8-like alpha-only class.
    assert RGBA8['alpha_only_format'] is False
    assert m.format_admit(RGBA8,RGBA8)['status']=='FORMAT_CONDITIONS_WITHIN_SCOPE'
