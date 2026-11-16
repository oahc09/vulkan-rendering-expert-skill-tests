"""Ordinary binding/arithmetic HOST contracts; no actual allocation or device proof."""
import re
U64=2**64-1
IDS={'buffer':{'offset':'01031','type':'01035','alignment':'01036','size':'01037','bound':'07459','required':'01444','dedicated':'01508'},'image':{'offset':'01046','type':'01047','alignment':'01048','size':'01049','bound':'07460','required':'01445','dedicated':'02628'}}
def u64(v):return type(v) is int and 0<=v<=U64
def identifier(v):return type(v) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,80}',v) is not None
def result(status,**kw):return {'status':status,'authority':'CALLER_FACTS_NOT_VERIFIED','complete_memory_validity':'NOT_INFERRED',**kw}
def bind(f):
 keys={'kind','resource_id','ordinary_scope_proven','allocation_creation_valid','same_device','requirements_size','requirements_alignment','memory_type_bits','memory_type_index','allocation_size','offset','already_bound','requires_dedicated','prefers_dedicated','dedicated'}
 if type(f) is not dict or set(f)!=keys:return result('UNKNOWN')
 if f['kind'] not in ('buffer','image') or not identifier(f['resource_id']):return result('UNKNOWN')
 for k in ('ordinary_scope_proven','allocation_creation_valid','same_device','already_bound','requires_dedicated','prefers_dedicated'):
  if type(f[k]) is not bool:return result('UNKNOWN')
 if not f['ordinary_scope_proven'] or not f['allocation_creation_valid'] or not f['same_device']:return result('UNKNOWN')
 if any(not u64(f[k]) for k in ('requirements_size','requirements_alignment','allocation_size','offset')):return result('UNKNOWN')
 size,align,alloc,off=(f[k] for k in ('requirements_size','requirements_alignment','allocation_size','offset'))
 if not size or not alloc or not align or align&(align-1):return result('UNKNOWN')
 if type(f['memory_type_bits']) is not int or not 0<f['memory_type_bits']<2**32 or type(f['memory_type_index']) is not int or not 0<=f['memory_type_index']<32:return result('UNKNOWN')
 d=f['dedicated']
 if d is not None and (type(d) is not dict or set(d)!={'kind','resource_id'} or d['kind'] not in ('buffer','image') or not identifier(d['resource_id'])):return result('UNKNOWN')
 # Allocations dedicated to the other resource category are outside this helper.
 if d is not None and d['kind']!=f['kind']:return result('UNKNOWN')
 kind=f['kind'];owner='vkBind'+kind.title()+'Memory';ids=[]
 def add(field,key):ids.append(f'VUID-{owner}-{field}-{IDS[kind][key]}')
 if f['already_bound']:add(kind,'bound')
 if off>=alloc:add('memoryOffset','offset')
 if not f['memory_type_bits']&(1<<f['memory_type_index']):add('memory','type')
 if off%align:add('memoryOffset','alignment')
 if size>alloc-off:add('size','size')
 match=d is not None and d['resource_id']==f['resource_id']
 if f['requires_dedicated'] and not match:add(kind,'required')
 if d is not None and (not match or off!=0):add('memory','dedicated')
 return result('BIND_CONDITIONS_WITHIN_SCOPE' if not ids else 'REJECTED',vuids=ids,normative_api_version='1.4.309',
               limits=['ordinary_scope excludes sparse, disjoint, external, protected, dedicated-image-aliasing/NV exceptions and unverified allocation API conditions.','Dedicated allocation creation validity remains separate. prefersDedicatedAllocation does not require dedication.'])

def granularity(a,b,granularity,simultaneous):
 keys={'allocation_id','offset','requirements_size','linear'}
 for r in (a,b):
  if type(r) is not dict or set(r)!=keys or not identifier(r['allocation_id']) or not u64(r['offset']) or not u64(r['requirements_size']) or not r['requirements_size'] or type(r['linear']) is not bool or r['offset']>U64-r['requirements_size']:return result('UNKNOWN')
 if type(simultaneous) is not bool or not u64(granularity) or not granularity or granularity&(granularity-1):return result('UNKNOWN')
 if a['allocation_id']!=b['allocation_id'] or a['offset']>=b['offset']:return result('UNKNOWN')
 if a['offset']+a['requirements_size']>b['offset']:return result('OUT_OF_SCOPE_OVERLAPPING_RANGES')
 if a['linear']==b['linear'] or not simultaneous:return result('NO_MIXED_SIMULTANEOUS_PAGE_CONDITION',binding_alignment_still_required=True)
 endpage=(a['offset']+a['requirements_size']-1)//granularity
 startpage=b['offset']//granularity
 return result('MIXED_PAGE_SEPARATION_SATISFIED' if endpage<startpage else 'ALIASING_RISK_NOT_BIND_VUID',end_page=endpage,start_page=startpage,
               limits=['Same allocation, ordered adjacent pair, simultaneous use, caller-proven resource class.','Not nonCoherentAtomSize, resident page size, minimum distance, or a complete aliasing/synchronization proof.'])

def free_obligations(f):
 keys={'bound_object_count','all_submitted_uses_retired','host_accesses_completed','no_future_bound_resource_use','reference_inventory_complete'}
 if type(f) is not dict or set(f)!=keys or type(f['bound_object_count']) is not int or not 0<=f['bound_object_count']<2**32 or any(type(f[k]) is not bool for k in keys-{'bound_object_count'}):return result('UNKNOWN')
 if not f['reference_inventory_complete']:return result('UNKNOWN')
 if not f['all_submitted_uses_retired']:return result('REJECTED',vuids=['VUID-vkFreeMemory-memory-00677'])
 if not f['host_accesses_completed'] or not f['no_future_bound_resource_use']:return result('LIFETIME_OBLIGATIONS_NOT_ESTABLISHED')
 return result('FREE_LIFETIME_OBLIGATIONS_DECLARED',bound_resources_may_remain=True,limits=['Not full allocator/handle/device validity. Bound resources cannot be used after their memory is freed.'])

def dedicated_allocation_size(kind,allocation_size,requirements_size,contract_version,ordinary_not_imported):
 """Version-specific size condition only; excludes imported-memory exceptions."""
 if type(kind) is not str or kind not in ('buffer','image') or not u64(allocation_size) or not u64(requirements_size) or not allocation_size or not requirements_size or ordinary_not_imported is not True or type(ordinary_not_imported) is not bool or contract_version not in ('1.4.309','1.4.368'):return result('UNKNOWN')
 valid=allocation_size==requirements_size if contract_version=='1.4.309' else allocation_size>=requirements_size
 return result('DEDICATED_SIZE_CONDITION_SATISFIED' if valid else 'REJECTED',contract_version=contract_version,
               predicate='EQUAL' if contract_version=='1.4.309' else 'GREATER_OR_EQUAL',
               vuids=[] if valid else [f'VUID-VkMemoryDedicatedAllocateInfo-{kind}-'+('02965' if kind=='buffer' else '02964')],
               limits=['Same VUID has different frozen text across versions; no equivalence or full allocation admission inferred.'])
