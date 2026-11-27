"""Bounded allocation-relative mapped-range preflight, not GPU completion proof.
No sparse/imported/device-group mapping; caller supplies true mapping and lifetime.
VK_WHOLE_SIZE is serialized only as the WHOLE string, never numeric UINT64_MAX.
"""
MAX=(1<<64)-1
WHOLE='VK_WHOLE_SIZE'
def uint(value,name,positive=False):
 if type(value) is not int or value<0 or value>MAX or (positive and value==0):raise ValueError(name)
 return value

def check_range(*,allocation_size,map_offset,map_size,offset,size,atom,mapped=True):
 for n,v in [('allocation_size',allocation_size),('map_offset',map_offset),('offset',offset),('atom',atom)]:uint(v,n,n in ('allocation_size','atom'))
 if atom & (atom-1):raise ValueError('atom must be power of two')
 if type(mapped) is not bool:raise ValueError('mapped fact required')
 if map_size==MAX or size==MAX:raise ValueError('serialize VK_WHOLE_SIZE as string')
 if map_size!=WHOLE:uint(map_size,'map_size',True)
 if size!=WHOLE:uint(size,'size')
 if map_offset>=allocation_size:raise ValueError('mapping starts outside allocation')
 end=allocation_size if map_size==WHOLE else map_offset+map_size
 if end>allocation_size:raise ValueError('mapping exceeds allocation')
 errors=[]
 if not mapped:errors.append('VUID-VkMappedMemoryRange-memory-00684')
 if offset%atom:errors.append('VUID-VkMappedMemoryRange-offset-00687')
 if size==WHOLE:
  if not map_offset<=offset<end:errors.append('VUID-VkMappedMemoryRange-size-00686')
  if end%atom and end!=allocation_size:errors.append('VUID-VkMappedMemoryRange-size-01389')
 else:
  if offset<map_offset or offset+size>end:errors.append('VUID-VkMappedMemoryRange-size-00685')
  if size%atom and offset+size!=allocation_size:errors.append('VUID-VkMappedMemoryRange-size-01390')
 return {'status':'INVALID_RANGE' if errors else 'VALID_RANGE_ONLY','vuids':errors,'effective_end':end if size==WHOLE else offset+size}

def expand_access(*,allocation_size,map_offset,map_size,offset,length,atom):
 uint(length,'length',True);uint(offset,'offset');uint(allocation_size,'allocation_size',True);uint(atom,'atom',True)
 if atom & (atom-1) or offset+length>allocation_size:raise ValueError('access/atom outside contract')
 start=offset//atom*atom;end=min(allocation_size,((offset+length+atom-1)//atom)*atom)
 check=check_range(allocation_size=allocation_size,map_offset=map_offset,map_size=map_size,offset=start,size=end-start,atom=atom)
 return {'status':'RANGE_READY_REQUIRES_ATOM_OWNERSHIP' if not check['vuids'] else 'REMAP_REQUIRED','offset':start,'size':end-start,'vuids':check['vuids'],'note':'allocation-relative; expanded neighboring bytes participate in synchronization'}

def visibility_obligations(*,direction,coherent,completed,host_dirty,access_exclusive,atom_exclusive,host_ordered,device_host_barrier):
 if direction not in ('upload','readback'):raise ValueError('direction')
 facts=(coherent,completed,host_dirty,access_exclusive,atom_exclusive,host_ordered,device_host_barrier)
 if any(type(v) is not bool for v in facts):raise ValueError('independently observed boolean facts required')
 if not access_exclusive:return {'status':'REJECTED_ACCESS_RACE'}
 if not coherent and not atom_exclusive:return {'status':'REJECTED_ATOM_RACE'}
 if not completed:return {'status':'WAIT_RELEVANT_DEVICE_USES'}
 if not host_ordered:return {'status':'REQUIRE_HOST_HAPPENS_BEFORE'}
 if direction=='upload':return {'status':'READY_WITHIN_FACTS','actions':[] if coherent else ['flush_before_submission'],'not_proven':['next submission dependencies','range validity','other queues/lifetime']}
 if not coherent and host_dirty:return {'status':'REJECTED_UNFLUSHED_HOST_WRITES'}
 if not device_host_barrier:return {'status':'REQUIRE_DEVICE_TO_HOST_DEPENDENCY'}
 return {'status':'READY_WITHIN_FACTS','actions':[] if coherent else ['invalidate_after_wait_before_read'],'not_proven':['range validity','unobserved queues/lifetime']}
