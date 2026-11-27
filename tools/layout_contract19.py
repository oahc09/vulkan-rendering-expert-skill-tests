"""Ordinary complete layout contracts over declared definitions, not Vulkan reflection.

Definition hashes stand for caller-proven identically-defined set layouts, not
handles or verified artifact bytes. Extension-special layouts/partial libraries,
shader interface validity and dynamic descriptors are not modeled.
"""
import re
SOURCE={'commit':'fa30d4e312e843193601be7cb926c7e25d9ec885','path':'chapters/descriptorsets.adoc','git_blob':'50a84ed1fe31cc00c8bf2d6d1fe72d20747d8d69','sha256':'3de692bf6e4f8579de50175be94c564a4580e1b8f0a59ed1e1267e1c3ca88950','anchor':'descriptors-compatibility'}
VU_SOURCE={'api_version':'1.4.309','sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'}
U32=(1<<32)-1
CORE_STAGES=63

def uint(v):return type(v) is int and 0<=v<=U32

def stages(v):return uint(v) and v>0 and v&~CORE_STAGES==0

def result(status,**kwargs):return {'status':status,'authority':'CALLER_DECLARED_DEFINITIONS_NOT_VERIFIED','whole_layout_validity':'NOT_INFERRED',**kwargs}

def push_ranges(ranges,max_size):
    if type(ranges) is not list or not uint(max_size) or max_size==0:return result('UNKNOWN')
    seen=0;ids=[]
    for r in ranges:
        if type(r) is not dict or set(r)!={'offset','size','stages'} or not uint(r['offset']) or not uint(r['size']) or not stages(r['stages']):return result('UNKNOWN')
        o,s=r['offset'],r['size']
        if o>=max_size:ids.append('VUID-VkPushConstantRange-offset-00294')
        if o%4:ids.append('VUID-VkPushConstantRange-offset-00295')
        if s==0:ids.append('VUID-VkPushConstantRange-size-00296')
        if s%4:ids.append('VUID-VkPushConstantRange-size-00297')
        if s>max_size-o:ids.append('VUID-VkPushConstantRange-size-00298')
        if seen&r['stages']:ids.append('VUID-VkPipelineLayoutCreateInfo-pPushConstantRanges-00292')
        seen|=r['stages']
    return result('RANGES_WITHIN_SCOPE' if not ids else 'REJECTED',vuids=sorted(set(ids)),normative_source=dict(VU_SOURCE))

def _layout(l):
    if type(l) is not dict or set(l)!={'scope','set_definitions','push_ranges','max_push_constants','independent_sets'}:return False
    if l['scope']!='ORDINARY_COMPLETE_LAYOUTS' or type(l['independent_sets']) is not bool:return False
    if type(l['set_definitions']) is not list or any(type(h) is not str or not re.fullmatch('[0-9a-f]{64}',h) for h in l['set_definitions']):return False
    return push_ranges(l['push_ranges'],l['max_push_constants'])['status']=='RANGES_WITHIN_SCOPE'

def _ranges(l):return sorted((r['offset'],r['size'],r['stages']) for r in l['push_ranges'])

def push_compatible(a,b):
    if not _layout(a) or not _layout(b):return result('UNKNOWN')
    return result('COMPATIBLE' if _ranges(a)==_ranges(b) else 'INCOMPATIBLE',source=dict(SOURCE))

def compatible(a,b,set_number):
    if not _layout(a) or not _layout(b) or not uint(set_number):return result('UNKNOWN')
    if set_number>=len(a['set_definitions']) or set_number>=len(b['set_definitions']):return result('UNKNOWN')
    same=(a['set_definitions'][:set_number+1]==b['set_definitions'][:set_number+1]
          and _ranges(a)==_ranges(b) and a['independent_sets']==b['independent_sets'])
    return result('COMPATIBLE' if same else 'INCOMPATIBLE',source=dict(SOURCE))

def bind_disturbance(previous,new_layout,set_number):
    """Single set bind; previous maps integer indices to binding layout declarations.

    Returns disturbed indices, not a complete command-buffer state machine. The
    new N binding replaces old N. No pipeline need be bound before this operation.
    Caller must mark disturbed descriptors undefined with the new layout; their
    future use is outside this one-step model. Pipeline binding alone is not this
    operation and does not mutate bindings.
    """
    if type(previous) is not dict or not _layout(new_layout) or not uint(set_number) or set_number>=len(new_layout['set_definitions']):return result('UNKNOWN')
    if any(not uint(i) or not _layout(l) or i>=len(l['set_definitions']) for i,l in previous.items()):return result('UNKNOWN')
    disturbed=[]
    for i,l in previous.items():
        if i<set_number:
            c=compatible(l,new_layout,i)['status']
            if c=='UNKNOWN':return result('UNKNOWN')
            if c=='INCOMPATIBLE':disturbed.append(i)
    if set_number in previous:
        c=compatible(previous[set_number],new_layout,set_number)['status']
        if c=='UNKNOWN':return result('UNKNOWN')
        if c=='INCOMPATIBLE':disturbed.extend(i for i in previous if i>set_number)
    return result('DISTURBANCE_EVALUATED',disturbed=sorted(disturbed),replaced=set_number,
                  requires_prebound_pipeline=False,source=dict(SOURCE))

def pipeline_access(binding_layout,pipeline_layout,set_number,undisturbed):
    if type(undisturbed) is not bool:return result('UNKNOWN')
    c=compatible(binding_layout,pipeline_layout,set_number)
    if c['status']=='UNKNOWN':return c
    return result('LAYOUT_ACCESS_PERMITTED' if undisturbed and c['status']=='COMPATIBLE' else 'LAYOUT_ACCESS_NOT_ESTABLISHED',bindings_mutated=False,
                  limits='Only compatibility and disturbance; actual descriptor validity remains separate.')

def push_update(layout_ranges,stage_mask,offset,size,max_size):
    """Validate byte/stage coverage in both directions, separate from creation.

    uint/alignment/bounds are preconditions; malformed update returns UNKNOWN
    rather than inventing a vkCmdPushConstants VUID from range-create VUIDs.
    No pushed values, command-buffer lifetime or shader access is inspected.
    """
    if push_ranges(layout_ranges,max_size)['status']!='RANGES_WITHIN_SCOPE':return result('UNKNOWN')
    if not stages(stage_mask) or not uint(offset) or not uint(size) or size==0 or offset%4 or size%4 or offset>=max_size or size>max_size-offset:return result('UNKNOWN')
    ids=[]
    for bit in (1,2,4,8,16,32):
        if stage_mask&bit and not any(r['stages']&bit and r['offset']<=offset and offset+size<=r['offset']+r['size'] for r in layout_ranges):
            ids.append('VUID-vkCmdPushConstants-offset-01795');break
    if any(r['offset']<offset+size and offset<r['offset']+r['size'] and r['stages']&~stage_mask for r in layout_ranges):ids.append('VUID-vkCmdPushConstants-offset-01796')
    return result('UPDATE_WITHIN_SCOPE' if not ids else 'REJECTED',vuids=ids,normative_source=dict(VU_SOURCE))
