"""Bounded opaque triangle BLAS/TLAS device build and compute ray query rules."""
import math

def scratch(*,address,buffer_address,buffer_size,required_size,alignment,storage_usage,bda_usage):
    for x in (address,buffer_address,buffer_size,required_size,alignment):
        if type(x) is not int or not 0<=x<=0xffffffffffffffff:raise ValueError('uint64 facts')
    if type(storage_usage) is not bool or type(bda_usage) is not bool:raise ValueError('usage flags')
    if not address or not buffer_address or not alignment or alignment&(alignment-1) or not required_size:return {'status':'UNKNOWN'}
    ids=[]
    if address%alignment:ids.append('VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-03710')
    if buffer_address>0xffffffffffffffff-buffer_size or address<buffer_address or required_size>buffer_size or address-buffer_address>buffer_size-required_size:ids.append('VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-03671')
    if not storage_usage:ids.append('VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-03674')
    if not bda_usage:return {'status':'BDA_NOT_ENABLED'}
    return {'status':'SCRATCH_WITHIN_SCOPE' if not ids else 'REJECTED','vuids':ids}

def create(*,offset,size,buffer_size,storage_usage):
    if type(storage_usage) is not bool or any(type(x) is not int or not 0<=x<=0xffffffffffffffff for x in (offset,size,buffer_size)):raise ValueError('typed facts')
    if not size or not buffer_size:return {'status':'OUT_OF_SCOPE'}
    ids=[]
    if offset%256:ids.append('VUID-VkAccelerationStructureCreateInfoKHR-offset-03734')
    # Frozen 1.4.309 validusage says less than buffer size, not current-version prose.
    if offset>0xffffffffffffffff-size or offset+size>=buffer_size:ids.append('VUID-VkAccelerationStructureCreateInfoKHR-offset-03616')
    if not storage_usage:return {'status':'OUT_OF_SCOPE'}
    return {'status':'CREATE_WITHIN_SCOPE' if not ids else 'REJECTED','vuids':ids}

def triangle_reference(origin,direction,tmin,tmax):
    """Fixed ordinary-scale geometry oracle, not a general robust geometry library."""
    if not isinstance(origin,(list,tuple)) or not isinstance(direction,(list,tuple)) or len(origin)!=3 or len(direction)!=3:raise ValueError('3-vectors')
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in [*origin,*direction,tmin,tmax]) or tmin<0 or tmax<=tmin or not any(direction):raise ValueError('finite ray interval')
    a=(-1.,-1.,0.);b=(1.,-1.,0.);c=(0.,1.,0.)
    sub=lambda a,b:[x-y for x,y in zip(a,b)]
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    cross=lambda a,b:[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    e1=sub(b,a);e2=sub(c,a);h=cross(direction,e2);det=dot(e1,h)
    if abs(det)<1e-12:return {'hit':False}
    inv=1/det;s=sub(origin,a);u=inv*dot(s,h)
    if u<0 or u>1:return {'hit':False}
    q=cross(s,e1);v=inv*dot(direction,q)
    if v<0 or u+v>1:return {'hit':False}
    t=inv*dot(e2,q)
    return {'hit':True,'t':t,'primitive':0,'customIndex':7} if tmin<=t<=tmax else {'hit':False}
