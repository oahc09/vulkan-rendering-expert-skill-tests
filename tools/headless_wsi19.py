"""Headless transfer-only swapchain admission and explicit present-fence retirement."""
def admit(m):
    ints={'minImages','maxImages','requestedImages','usage','supportedUsage','presentMode','format','colorSpace','selectedTransform','supportedTransforms','selectedCompositeAlpha','supportedCompositeAlpha','maxLayers'}
    arrays={'extent','minExtent','maxExtent','currentExtent','presentModes','formats'}
    bools={'presentSupported','swapchainEnabled','maintenanceSupported','maintenanceEnabled'}
    if not isinstance(m,dict) or set(m)!=ints|arrays|bools:return {'status':'UNKNOWN'}
    if any(type(m[k]) is not bool for k in bools) or any(type(m[k]) is not int or not 0<=m[k]<=0xffffffff for k in ints):raise ValueError('typed capabilities')
    for k in ('extent','minExtent','maxExtent','currentExtent'):
        if not isinstance(m[k],list) or len(m[k])!=2 or any(type(v) is not int or not 0<=v<=0xffffffff for v in m[k]):raise ValueError('extent facts')
    if not isinstance(m['presentModes'],list) or any(type(v) is not int or not 0<=v<=0xffffffff for v in m['presentModes']) or not isinstance(m['formats'],list) or any(not isinstance(x,list) or len(x)!=2 or any(type(v) is not int or not 0<=v<=0xffffffff for v in x) for x in m['formats']):raise ValueError('format/mode facts')
    if not m['presentSupported'] or not m['swapchainEnabled']:return {'status':'UNSUPPORTED_PRESENT'}
    if not m['maintenanceSupported'] or not m['maintenanceEnabled']:return {'status':'PRESENT_RETIREMENT_UNAVAILABLE'}
    if m['usage']!=3 or m['presentMode']!=2 or m['maxLayers']<1:return {'status':'OUT_OF_SCOPE'}
    if m['supportedUsage']&m['usage']!=m['usage'] or m['presentMode'] not in m['presentModes'] or [m['format'],m['colorSpace']] not in m['formats']:return {'status':'UNSUPPORTED_CONFIGURATION'}
    if m['format'] not in (37,44) or m['colorSpace']!=0:return {'status':'OUT_OF_SCOPE'}
    if any(not m[k] or m[k]&(m[k]-1) or not(m[k]&m[s]) for k,s in [('selectedTransform','supportedTransforms'),('selectedCompositeAlpha','supportedCompositeAlpha')]):return {'status':'UNSUPPORTED_CONFIGURATION'}
    if not m['minImages'] or not m['requestedImages'] or m['requestedImages']<m['minImages'] or (m['maxImages']!=0 and m['requestedImages']>m['maxImages']):return {'status':'INVALID_IMAGE_COUNT'}
    if not all(0<v and lo<=v<=hi for v,lo,hi in zip(m['extent'],m['minExtent'],m['maxExtent'])):return {'status':'INVALID_EXTENT'}
    if m['currentExtent']!=[0xffffffff,0xffffffff] and m['extent']!=m['currentExtent']:return {'status':'FIXED_SURFACE_EXTENT'}
    return {'status':'HEADLESS_WSI_WITHIN_SCOPE','physical_display':'NOT_PROVEN'}

def acquired(result):
    if type(result) is not int:raise ValueError('VkResult integer')
    if result in (0,1000001003):return {'usable_image':True,'recreate_after_retirement':result!=0}
    return {'usable_image':False,'action':{1:'RETRY_WITHOUT_WAIT',2:'RETRY_WITHOUT_WAIT',-1000001004:'RECREATE',-1000000000:'RECREATE_SURFACE',-4:'DEVICE_LOST'}.get(result,'STOP_UNKNOWN')}

def retirement(*,generation,current_generation,render_fence,present_fence,queue_idle=False):
    if any(type(v) is not int or v<0 for v in (generation,current_generation)) or any(type(v) is not bool for v in (render_fence,present_fence,queue_idle)):raise ValueError('retirement facts')
    if generation!=current_generation:return {'status':'STALE_GENERATION'}
    if not render_fence or not present_fence:return {'status':'WAIT_RETIREMENT'}
    return {'status':'SERIAL_PRESENT_RETIRED','physical_display':'NOT_PROVEN'}
