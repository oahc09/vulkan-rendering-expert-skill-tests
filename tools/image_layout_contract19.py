"""Modeled ordinary COLOR subresource layout effects over caller-established facts.
No Vulkan state or access masks are inspected. Output is not an executed state.
"""
import copy
LAYOUTS={'UNDEFINED','PREINITIALIZED','GENERAL','COLOR_ATTACHMENT_OPTIMAL','SHADER_READ_ONLY_OPTIMAL','TRANSFER_SRC_OPTIMAL','TRANSFER_DST_OPTIMAL'}
SOURCE={'commit':'fa30d4e312e843193601be7cb926c7e25d9ec885','path':'chapters/synchronization.adoc','sha256':'7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909','anchors':['synchronization-image-layout-transitions','synchronization-image-barrier2-ignored-layout','synchronization-image-barrier-ignored-layout']}
VU_SOURCE={'api_version':'1.4.309','sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'}
FACT_KEYS={'ordinary_2d_color','no_aliasing_or_external_ownership','subresource_selection_valid','layout_usage_and_api_valid','prior_accesses_ordered_before_transition','prior_writes_available','next_accesses_ordered_after_transition','transition_writes_visible_to_next_access','ignored_barrier_dependencies_sufficient'}
BARRIER_KEYS={'api','sync2_enabled','source_family','destination_family','old_layout','new_layout','subresources'}

def uint(v):return type(v) is int and 0<=v<2**32

def cell(v):return type(v) in (list,tuple) and len(v)==2 and all(uint(x) for x in v)

def result(status,**kw):
    return {'status':status,'authority':'CALLER_DECLARED_NOT_DEVICE_VERIFIED','source':dict(SOURCE),'vuids':[],
            'limitations':['Ordinary 2D COLOR cells only; no ownership transfer, alias, 3D slice or depth/stencil reasoning.',
                          'Scope, API/usage validity, availability and visibility are independent caller-proven facts, not mask analysis.',
                          'State effects are modeled, not a command execution or full barrier/domain acceptance.',
                          'defined=False means contents may no longer be relied on; UNDEFINED permits discard but does not promise clearing or modification.'],**kw}

def evaluate(state,barrier,facts):
    """State list entries: mip,layer,layout,defined; selected cells are explicit pairs.

    Unknown/malformed facts never update state. Unsatisfied dependency facts also
    yield no modeled state. Actual current layout need not equal an ignored value.
    """
    if type(state) is not list or not state or type(barrier) is not dict or set(barrier)!=BARRIER_KEYS or type(facts) is not dict or set(facts)!=FACT_KEYS:return result('UNKNOWN')
    if any(type(v) is not bool for v in facts.values()):return result('UNKNOWN')
    if not all(facts[k] for k in ('ordinary_2d_color','no_aliasing_or_external_ownership','subresource_selection_valid','layout_usage_and_api_valid')):return result('UNKNOWN')
    if type(barrier['api']) is not str or barrier['api'] not in ('legacy','barrier2') or type(barrier['sync2_enabled']) is not bool:return result('UNKNOWN')
    if barrier['api']=='barrier2' and not barrier['sync2_enabled']:return result('UNKNOWN')
    families=[barrier['source_family'],barrier['destination_family']]
    if any(not uint(f) or f in (0xfffffffc,0xfffffffd,0xfffffffe) for f in families) or families[0]!=families[1]:return result('UNKNOWN')
    if any(type(barrier[k]) is not str or barrier[k] not in LAYOUTS for k in ('old_layout','new_layout')):return result('UNKNOWN')
    cells={}
    for r in state:
        if type(r) is not dict or set(r)!={'mip','layer','layout','defined'} or not uint(r['mip']) or not uint(r['layer']) or type(r['layout']) is not str or r['layout'] not in LAYOUTS or type(r['defined']) is not bool:return result('UNKNOWN')
        key=(r['mip'],r['layer'])
        if key in cells:return result('UNKNOWN')
        if r['layout']=='UNDEFINED' and r['defined']:return result('UNKNOWN')
        cells[key]=r
    selection=barrier['subresources']
    if type(selection) is not list or not selection or any(not cell(s) for s in selection):return result('UNKNOWN')
    selected=[tuple(s) for s in selection]
    if len(set(selected))!=len(selected) or any(s not in cells for s in selected):return result('UNKNOWN')
    old,new=barrier['old_layout'],barrier['new_layout']
    ignored=barrier['sync2_enabled'] and old==new
    if ignored:
        if not facts['ignored_barrier_dependencies_sufficient']:return result('INSUFFICIENT_DEPENDENCY',layouts_ignored=True)
        return result('MODELED_LAYOUTS_IGNORED',layouts_ignored=True,content_preservation_not_guaranteed=False,state_after=copy.deepcopy(state))
    owner='VkImageMemoryBarrier2' if barrier['api']=='barrier2' else 'VkImageMemoryBarrier'
    ids=[]
    if old!='UNDEFINED' and any(cells[s]['layout']!=old for s in selected):ids.append(f'VUID-{owner}-oldLayout-01197')
    if new in ('UNDEFINED','PREINITIALIZED'):ids.append(f'VUID-{owner}-newLayout-01198')
    if ids:return result('REJECTED',vuids=ids,normative_source=dict(VU_SOURCE))
    needed=('prior_accesses_ordered_before_transition','prior_writes_available','next_accesses_ordered_after_transition','transition_writes_visible_to_next_access')
    missing=[k for k in needed if not facts[k]]
    if missing:return result('INSUFFICIENT_DEPENDENCY',missing=missing,discard_does_not_remove_dependencies=old=='UNDEFINED')
    updated=copy.deepcopy(state)
    for r in updated:
        if (r['mip'],r['layer']) in selected:
            r['layout']=new
            if old=='UNDEFINED':r['defined']=False
    return result('MODELED_TRANSITION',layouts_ignored=False,content_preservation_not_guaranteed=old=='UNDEFINED',state_after=updated)
