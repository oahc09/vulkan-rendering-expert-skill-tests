"""Non-null, non-sparse, ordinary uniform-buffer descriptor preflight only."""
WHOLE=(1<<64)-1
def check(*,buffer_size,offset,range_bytes,max_range,alignment,bound,uniform_usage,update_safe):
 for x in (buffer_size,offset,range_bytes):
  if type(x) is not int or not 0<=x<=WHOLE:raise ValueError('VkDeviceSize required')
 for x in (max_range,alignment):
  if x is not None and (type(x) is not int or x<=0 or x>WHOLE):raise ValueError('positive queried limit required')
 if max_range is not None and max_range>=2**32:raise ValueError('uint32 maxUniformBufferRange required')
 for x in (bound,uniform_usage,update_safe):
  if x is not None and type(x) is not bool:raise ValueError('tri-state fact expected')
 ids=[];unknown=[];policy=[]
 if offset>=buffer_size:ids.append('VUID-VkDescriptorBufferInfo-offset-00340')
 if range_bytes!=WHOLE and range_bytes==0:ids.append('VUID-VkDescriptorBufferInfo-range-00341')
 if range_bytes!=WHOLE and range_bytes>max(0,buffer_size-offset):ids.append('VUID-VkDescriptorBufferInfo-range-00342')
 effective=buffer_size-offset if range_bytes==WHOLE else range_bytes
 if alignment is None:unknown.append('minUniformBufferOffsetAlignment')
 elif offset%alignment:ids.append('VUID-VkWriteDescriptorSet-descriptorType-00327')
 if max_range is None:unknown.append('maxUniformBufferRange')
 elif effective>max_range:ids.append('VUID-VkWriteDescriptorSet-descriptorType-00332')
 for fact,name,vuid in [(bound,'complete binding','00329'),(uniform_usage,'uniform usage','00330')]:
  if fact is None:unknown.append(name)
  elif not fact:ids.append('VUID-VkWriteDescriptorSet-descriptorType-'+vuid)
 if update_safe is None:unknown.append('ordinary descriptor update lifetime not established')
 elif update_safe is False:policy.append('known unsafe ordinary descriptor update')
 return dict(status='REJECTED' if ids or policy else 'UNKNOWN' if unknown else 'WITHIN_CHECKED_SCOPE',vuids=ids,policy_rejections=policy,unknown=unknown,effective_range=effective if effective>=0 else None,limitations=['ordinary non-null non-sparse UBO only','pool/layout/write counts and shader access not checked','dynamic offsets/indexing/descriptor buffers excluded'])
