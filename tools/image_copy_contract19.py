"""Partial single-plane color-copy contracts, using caller-proven format metadata.

No format lookup, feature query, Vulkan execution or automatic destination-offset
conversion occurs. Local image regions must already be expressed in that image's
texel coordinates. A valid local region is NOT a complete VkImageCopy admission.
"""
SOURCE={'commit':'fa30d4e312e843193601be7cb926c7e25d9ec885',
        'formats':{'path':'chapters/formats.adoc','anchor':'formats-size-compatibility','git_blob':'1f9d7a8b731ac6aa433533854daaadaa1faf46bc','sha256':'9360d12ae4c69c9eb7cf374dc3c99c061b6386f1551b9b4648d14728101cb7f1'},
        'copies':{'path':'chapters/copies.adoc','anchor':'copies-images-addressing','git_blob':'4119fb54316db54ca3c173a917998ce8f1fba0ac','sha256':'b821b4b219c3e7e691332b651c40cd169b74017d7212aad9d1ddbeef8acbec05'}}
VU_SOURCE={'api_version':'1.4.309','sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'}
LIMITS=['Caller-proven format metadata and local coordinates only; not actual format support verification.',
        'Excludes alpha-only formats such as A8 (not ordinary RGBA alpha channels), depth/stencil, multiplanar, special extension behavior and pNext.',
        'Queue transfer granularity, layouts, synchronization, usage, samples, aliasing and image-type conversions are not proven.',
        'Destination offsets/extents require size adjustment per frozen prose; this tool does not infer unique VkImageCopy destination coordinates.',
        'No decompression or numeric/color conversion is performed; no whole-copy or domain acceptance.']

def result(status,**kwargs):return {'status':status,'authority':'CALLER_DECLARED_NOT_VERIFIED','limits':list(LIMITS),**kwargs}
def u32(v):return type(v) is int and 0<=v<2**32
def vector(v,positive=True):return type(v) in (list,tuple) and len(v)==3 and all(u32(x) and (x>0 or not positive) for x in v)

def metadata(m):
    if type(m) is not dict or set(m)!={'color','single_plane','alpha_only_format','supported','compressed','block_extent','block_bytes'}:return False
    if any(type(m[k]) is not bool for k in ('color','single_plane','alpha_only_format','supported','compressed')):return False
    if not m['color'] or not m['single_plane'] or m['alpha_only_format'] or not m['supported']:return False
    if not vector(m['block_extent']) or not u32(m['block_bytes']) or m['block_bytes']==0:return False
    if not m['compressed'] and tuple(m['block_extent'])!=(1,1,1):return False
    return True

def format_admit(source,destination):
    if not metadata(source) or not metadata(destination):return result('UNKNOWN')
    ids=[]
    if source['block_bytes']!=destination['block_bytes']:ids.append('VUID-vkCmdCopyImage-srcImage-01548')
    if source['compressed'] and destination['compressed'] and tuple(source['block_extent'])!=tuple(destination['block_extent']):ids.append('VUID-vkCmdCopyImage-srcImage-09247')
    return result('FORMAT_CONDITIONS_WITHIN_SCOPE' if not ids else 'REJECTED',vuids=ids,normative_source=dict(VU_SOURCE))

def representation_blocks_equal(source_extent,destination_extent,source_block,destination_block):
    """Evaluate ceil(A/a)=ceil(X/x); not a construction of unique X or offsets.

    Deliberately independent of copy format admission: two compressed formats can
    have equal block counts but still fail copy's same-block-extent requirement.
    """
    if not all(vector(v) for v in (source_extent,destination_extent,source_block,destination_block)):return result('UNKNOWN')
    a=[(n+b-1)//b for n,b in zip(source_extent,source_block)]
    x=[(n+b-1)//b for n,b in zip(destination_extent,destination_block)]
    return result('BLOCK_COUNTS_EQUAL' if a==x else 'BLOCK_COUNTS_DIFFER',source_blocks=a,destination_blocks=x,
                  unique_destination_extent_inferred=False,source=SOURCE['formats'])

def image_region(fmt,offset,extent,mip_extent,side):
    """One region in ONE image's local texel coordinates, never raw mixed coordinates.

    For destination, the caller must first establish size-adjusted destination
    coordinates. Exact offset alignment is separate from extent's mip-edge
    exception: reaching the edge never excuses a misaligned offset. VUID labels
    denote frozen rule families, not predictions of Validation-layer output.
    """
    if not metadata(fmt) or not vector(extent) or not vector(mip_extent) or type(side) is not str or side not in ('src','dst'):return result('UNKNOWN')
    if type(offset) not in (list,tuple) or len(offset)!=3 or any(type(o) is not int or not -(2**31)<=o<2**31 for o in offset):return result('UNKNOWN')
    ids=[];bounds=[]
    offset_base=7278 if side=='src' else 7281
    extent_base=1728 if side=='src' else 1732
    for axis,(o,n,m,b) in enumerate(zip(offset,extent,mip_extent,fmt['block_extent'])):
        if o<0 or o>=m or o+n>m:bounds.append(axis)
        if o%b:ids.append(f'VUID-vkCmdCopyImage-pRegions-{offset_base+axis:05}')
        if o+n!=m and n%b:ids.append(f'VUID-vkCmdCopyImage-{side}Image-{extent_base+axis:05}')
    return result('LOCAL_REGION_CONDITIONS_WITHIN_SCOPE' if not ids and not bounds else 'REJECTED',
                  vuids=ids,out_of_bounds_axes=bounds,coordinate_space='THIS_IMAGE_LOCAL_TEXELS',
                  normative_source=dict(VU_SOURCE),complete_copy_admission=False)
