"""Bounded physical-storage address admission. Metadata is not GPU execution proof."""
U64_MAX=(1<<64)-1

def validate_range(*,base,size,address,length,alignment,live,retired):
    """Non-sparse single buffer, one known allocation generation, no capture replay."""
    for k,v in dict(base=base,size=size,address=address,length=length,alignment=alignment).items():
        if type(v) is not int or not 0<=v<=U64_MAX:raise ValueError(k+' must be uint64')
    if type(live) is not bool or type(retired) is not bool:raise ValueError('lifetime facts')
    if not live:return {'status':'DEAD_ALLOCATION'}
    if retired:return {'status':'RETIRED_GENERATION'}
    if not alignment or alignment&(alignment-1):raise ValueError('power-of-two alignment')
    if not base or not address or not size or not length:return {'status':'INVALID_RANGE'}
    if base>U64_MAX-size or address>U64_MAX-length:return {'status':'ADDRESS_OVERFLOW'}
    if address%alignment:return {'status':'MISALIGNED_ADDRESS'}
    if address<base or address+length>base+size:return {'status':'OUT_OF_BOUNDS'}
    return {'status':'ADDRESS_WITHIN_KNOWN_LIVE_BUFFER','robustness_guarantee':False}

def admit(*,supported,enabled,shader_int64_enabled,usage,allocation_flags,bound,api_version):
    if any(type(v) is not bool for v in (supported,enabled,shader_int64_enabled,bound)):raise ValueError('typed feature facts')
    if any(type(v) is not int or v<0 or v>0xffffffff for v in (usage,allocation_flags,api_version)):raise ValueError('uint32 facts')
    if api_version>>29 or api_version<4202496:return {'status':'OUT_OF_SCOPE_CORE_1_2'}
    if not supported:return {'status':'UNSUPPORTED'}
    if not enabled or not shader_int64_enabled:return {'status':'FEATURE_NOT_ENABLED'}
    if usage&0x20000==0:return {'status':'MISSING_ADDRESS_USAGE','vuid':'VUID-VkBufferDeviceAddressInfo-buffer-02601'}
    if allocation_flags&2==0:return {'status':'MISSING_ADDRESS_ALLOCATION'}
    if not bound:return {'status':'BUFFER_NOT_BOUND'}
    return {'status':'BDA_PREREQUISITES_WITHIN_SCOPE','shader_execution':'NOT_PROVEN'}

def retire(*,submitted,write_visible,fence_complete):
    if any(type(v) is not bool for v in (submitted,write_visible,fence_complete)):raise ValueError('typed retirement facts')
    if not submitted:return {'status':'NOT_SUBMITTED'}
    if not fence_complete:return {'status':'KEEP_BUFFERS_AND_POINTER_TABLE_LIVE'}
    if not write_visible:return {'status':'HOST_VISIBILITY_NOT_PROVEN'}
    return {'status':'BOUNDED_READBACK_READY'}

def special_availability(extensions,required):
    """No auto fallback: absence is unavailable; presence still needs feature/profile queries."""
    if not isinstance(extensions,dict) or any(not isinstance(k,str) or type(v) is not bool for k,v in extensions.items()):raise ValueError('extension inventory')
    if not isinstance(required,list) or not required or any(not isinstance(x,str) for x in required):raise ValueError('required owners')
    missing=[x for x in required if x not in extensions]
    if missing:return {'status':'NOT_QUERIED','owners':missing}
    absent=[x for x in required if not extensions[x]]
    if absent:return {'status':'UNSUPPORTED_EXTENSION','owners':absent,'executed':False}
    return {'status':'FEATURE_PROFILE_QUERY_REQUIRED','executed':False}
