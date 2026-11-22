"""Bounded two-element ordinary dynamic UBO array and ring retirement policy."""
def bind(m,offsets):
 keys=('alignment','bufferSize','descriptorCount','range','baseOffset','maxUniformRange','maxDynamicUBO','maxStageUBO')
 if not isinstance(m,dict) or any(k not in m for k in keys) or not isinstance(offsets,list):return {'status':'UNKNOWN'}
 if any(type(m[k]) is not int or m[k]<0 or m[k]>0xffffffffffffffff for k in keys):raise ValueError('integer facts required')
 for k in ('descriptorCount','maxUniformRange','maxDynamicUBO','maxStageUBO'):
  if m[k]>0xffffffff:raise ValueError('uint32 limit')
 if m['alignment']<1:raise ValueError('alignment')
 if m['descriptorCount']!=2 or m['range']!=16 or m['baseOffset']!=0:return {'status':'OUT_OF_SCOPE'}
 if any(type(o) is not int or o<0 or o>0xffffffff for o in offsets):raise ValueError('uint32 offsets')
 if min(m['maxDynamicUBO'],m['maxStageUBO'])<2 or m['maxUniformRange']<16:return {'status':'UNSUPPORTED_LIMITS'}
 v=[]
 if len(offsets)!=2:v.append('VUID-vkCmdBindDescriptorSets-dynamicOffsetCount-00359')
 if any(o%m['alignment'] for o in offsets):v.append('VUID-vkCmdBindDescriptorSets-pDynamicOffsets-01971')
 if any(m['baseOffset']+o+m['range']>m['bufferSize'] for o in offsets):v.append('VUID-vkCmdBindDescriptorSets-pDescriptorSets-01979')
 return {'status':'REJECTED' if v else 'BIND_WITHIN_SCOPE','vuids':v,'order':'set0 binding0 array element0, then element1; semantic role is not checked by Validation'}
def reuse(*,slot_generation,observed_generation,prior_frame,completed_frames):
 if type(slot_generation) is not int or type(observed_generation) is not int or min(slot_generation,observed_generation)<0 or not isinstance(completed_frames,list) or any(type(f) is not int or f<0 for f in completed_frames):raise ValueError('generation/completion facts')
 if slot_generation!=observed_generation:return {'status':'STALE_GENERATION'}
 if prior_frame is not None and (type(prior_frame) is not int or prior_frame<0):raise ValueError('prior frame')
 if prior_frame is not None and prior_frame not in completed_frames:return {'status':'WAIT_RETIREMENT'}
 return {'status':'REUSE_WITHIN_SCOPE','limitation':'caller must bind same buffer/slot/run and real fence coverage; CPU policy does not observe GPU races'}
