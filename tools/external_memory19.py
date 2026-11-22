"""Bounded Vulkan-origin OPAQUE_FD buffer admission and application FD ownership.
No external execution, cache visibility, semaphore or physical GPU claim.
"""
def admit(m):
    keys={'handleType','usage','flags','exportFeatures','importFeatures','exportCompatible','importCompatible','exportTypes','importTypes','memoryTypeIndex','importMemoryTypeIndex','exportRequirementSize','importRequirementSize','exportBufferSize','importBufferSize','exportSharingMode','importSharingMode','exportHandleTypes','importHandleTypes','exportSize','importSize','exportRequiresDedicated','importRequiresDedicated','exportDedicated','importDedicated','sameDeviceUUID','sameDriverUUID','memoryFdEnabled'}
    if not isinstance(m,dict) or set(m)!=keys:return {'status':'UNKNOWN'}
    boolean={'exportRequiresDedicated','importRequiresDedicated','exportDedicated','importDedicated','sameDeviceUUID','sameDriverUUID','memoryFdEnabled'}
    for k in boolean:
        if type(m[k]) is not bool:raise ValueError('boolean facts required: '+k)
    for k in keys-boolean:
        if type(m[k]) is not int or not 0<=m[k]<=(0xffffffffffffffff if k.endswith('Size') else 0xffffffff):raise ValueError('unsigned facts required: '+k)
    if (m['handleType'],m['usage'],m['flags'])!=(1,3,0):return {'status':'OUT_OF_SCOPE'}
    if not m['memoryFdEnabled'] or m['exportFeatures']&2!=2 or m['importFeatures']&4!=4 or m['exportCompatible']&1!=1 or m['importCompatible']&1!=1:return {'status':'UNSUPPORTED_HANDLE'}
    if not m['sameDeviceUUID'] or not m['sameDriverUUID']:return {'status':'INCOMPATIBLE_IDENTITY'}
    if m['importMemoryTypeIndex']!=m['memoryTypeIndex']:return {'status':'INCOMPATIBLE_MEMORY_TYPE'}
    if m['memoryTypeIndex']>=32 or not (m['exportTypes']&m['importTypes']&(1<<m['memoryTypeIndex'])):return {'status':'INCOMPATIBLE_MEMORY_TYPE'}
    if m['exportBufferSize']!=m['importBufferSize'] or not m['exportBufferSize'] or m['exportSharingMode']!=0 or m['importSharingMode']!=0 or m['exportHandleTypes']!=1 or m['importHandleTypes']!=1:return {'status':'OUT_OF_SCOPE'}
    if m['exportSize']<m['exportRequirementSize'] or m['importSize']<m['importRequirementSize']:return {'status':'INCOMPATIBLE_ALLOCATION'}
    if not m['exportSize'] or m['exportSize']!=m['importSize']:return {'status':'INCOMPATIBLE_ALLOCATION'}
    if ((m['exportFeatures']&1 or m['exportRequiresDedicated']) and not m['exportDedicated']) or ((m['importFeatures']&1 or m['importRequiresDedicated']) and not m['importDedicated']):return {'status':'DEDICATED_REQUIRED'}
    if (m['exportDedicated'] and m['exportSize']!=m['exportRequirementSize']) or (m['importDedicated'] and m['importSize']!=m['importRequirementSize']):return {'status':'INCOMPATIBLE_ALLOCATION'}
    if m['exportDedicated']!=m['importDedicated']:return {'status':'OUT_OF_SCOPE'}
    return {'status':'MEMORY_IMPORT_WITHIN_SCOPE','execution_visibility':'NOT_PROVEN','scope':'same physical device/driver; identical exclusive transfer buffers, Vulkan-origin OPAQUE_FD; size/type matched to exporting allocation'}

def transition(state,event):
    """Pure caller-side bookkeeping; never probes or closes an actual FD."""
    allowed={('ABSENT','export_success'):'APP_OWNED',('APP_OWNED','import_success'):'IMPLEMENTATION_OWNED',('APP_OWNED','import_failure'):'APP_OWNED',('APP_OWNED','query_aborted'):'APP_OWNED',('APP_OWNED','close'):'CLOSED'}
    if not isinstance(state,str) or not isinstance(event,str):raise ValueError('state/event strings')
    if (state,event) not in allowed:return {'status':'REJECTED_OWNERSHIP_TRANSITION','state':state}
    return {'status':'TRANSITION_ALLOWED','state':allowed[state,event]}
