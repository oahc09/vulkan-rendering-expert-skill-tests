"""Bounded ordinary uint32 SSBO robustness2; no BDA, atomics or pipeline overrides."""
def access(*,descriptor_range,alignment,byte_offset,operation,prior_same_address_store=False,volatile=False):
    # Generic rounding semantics; actual SSBO admission below restricts alignment to 1/4.
    for v in (descriptor_range,alignment,byte_offset):
        if type(v) is not int or not 0<=v<=0xffffffffffffffff:raise ValueError('uint64 facts')
    if descriptor_range==0 or alignment==0 or alignment&(alignment-1) or byte_offset%4:raise ValueError('range/alignment/uint32 access')
    if type(prior_same_address_store) is not bool or type(volatile) is not bool:raise ValueError('boolean facts')
    if operation not in ('load','store'):return {'status':'OUT_OF_SCOPE'}
    if byte_offset>0xffffffffffffffff-4 or descriptor_range>0xffffffffffffffff-(alignment-1):return {'status':'OUT_OF_SCOPE'}
    rounded=(descriptor_range+alignment-1)//alignment*alignment
    if byte_offset+4<=descriptor_range:return {'status':'IN_BOUNDS','rounded_range':rounded}
    if operation=='load' and prior_same_address_store and not volatile:return {'status':'PRIOR_STORE_VALUE_PERMITTED','rounded_range':rounded}
    if byte_offset<rounded:return {'status':'PADDING_OR_PARTIAL_NO_STRICT_ORACLE','rounded_range':rounded}
    return {'status':'ZERO_REQUIRED' if operation=='load' else 'DISCARD_REQUIRED','rounded_range':rounded}

def admit(m):
    booleans={'extensionSupported','extensionEnabled','coreSupported','coreEnabled','robust2Supported','robust2Enabled','nullSupported','nullEnabled','ordinarySSBO','pipelineOverrideAbsent'}
    numbers={'storageAlignment','descriptorRange','sourceBufferSize','sourceOffset','maxStorageRange','maxStageStorageBuffers','maxSetStorageBuffers','readIndex','writeIndex','outputRange'}
    if not isinstance(m,dict) or set(m)!=booleans|numbers:return {'status':'UNKNOWN'}
    if any(type(m[k]) is not bool for k in booleans):raise ValueError('boolean facts')
    if any(type(m[k]) is not int or not 0<=m[k]<=0xffffffffffffffff for k in numbers):raise ValueError('unsigned facts')
    if any(m[k]>0xffffffff for k in ('maxStageStorageBuffers','maxSetStorageBuffers','maxStorageRange','readIndex','writeIndex')):raise ValueError('uint32 limit/index')
    if not all(m[k] for k in ('ordinarySSBO','pipelineOverrideAbsent')):return {'status':'OUT_OF_SCOPE'}
    if not all(m[k] for k in ('extensionSupported','coreSupported','robust2Supported','nullSupported')):return {'status':'UNSUPPORTED'}
    if m['robust2Enabled'] and not m['coreEnabled']:return {'status':'REJECTED','vuids':['VUID-VkPhysicalDeviceRobustness2FeaturesEXT-robustBufferAccess2-04000']}
    if not all(m[k] for k in ('extensionEnabled','coreEnabled','robust2Enabled','nullEnabled')):return {'status':'NOT_ENABLED'}
    r=m['descriptorRange'];a=m['storageAlignment']
    if a not in (1,4):raise ValueError('storage robustness2 alignment must be 1 or 4')
    if r<16 or r%4 or r%a or m['sourceOffset']!=0 or m['outputRange']!=16 or m['sourceBufferSize']!=r+16 or r>m['maxStorageRange'] or min(m['maxStageStorageBuffers'],m['maxSetStorageBuffers'])<3:return {'status':'OUT_OF_SCOPE'}
    if m['readIndex']!=r//4 or m['writeIndex']!=r//4+1:return {'status':'OUT_OF_SCOPE'}
    read=access(descriptor_range=r,alignment=a,byte_offset=m['readIndex']*4,operation='load')
    write=access(descriptor_range=r,alignment=a,byte_offset=m['writeIndex']*4,operation='store')
    return {'status':'ROBUST2_BUFFER_WITHIN_SCOPE','read':read,'write':write,'null_access':'zero loads; stores discarded; not classified as out-of-bounds','scope':'query/enable metadata only; actual shader ordering, synchronization and readback verified separately'}

def null_update(*,enabled,is_null,offset,whole_size):
    if any(type(v) is not bool for v in (enabled,is_null,whole_size)) or type(offset) is not int or not 0<=offset<=0xffffffffffffffff:raise ValueError('typed facts')
    if not is_null:return {'status':'OUT_OF_SCOPE'}
    ids=[]
    if not enabled:ids.append('VUID-VkDescriptorBufferInfo-buffer-02998')
    if offset!=0 or not whole_size:ids.append('VUID-VkDescriptorBufferInfo-buffer-02999')
    return {'status':'REJECTED' if ids else 'NULL_UPDATE_WITHIN_SCOPE','vuids':ids}
