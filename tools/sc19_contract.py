"""Bounded SC host preflight rules, NOT SC API execution or certification."""

def u64(x):
 if type(x) is not int or not 0<=x<2**64:raise ValueError('unsigned integer expected')
 return x

def u32(x):
 u64(x)
 if x>=2**32:raise ValueError('uint32 API field expected')
 return x

def pipeline_pool(*,requested_size,reservations,current_count,total_ever_created,recycle):
 """05028/05029/05030, excluding other pipeline-creation requirements."""
 if recycle is not None and type(recycle) is not bool:raise ValueError('tri-state recycle property required')
 size=u64(requested_size);current=u64(current_count);total=u64(total_ever_created)
 if not size or current>total:raise ValueError('invalid size/history')
 capacity=0;found=False
 for row in reservations:
  s=u64(row['poolEntrySize']);n=u32(row['poolEntryCount'])
  if not s:raise ValueError('zero entry size')
  if s==size:capacity+=n;found=True
 if not found:return dict(status='REJECTED',rule='05028',reason='size was not reserved')
 if recycle is None:return dict(status='UNKNOWN',rule='05029/05030',reason='actual recyclePipelineMemory unavailable')
 used=current if recycle else total
 return dict(status='WITHIN_POOL_COUNT_ONLY' if used+1<=capacity else 'REJECTED',rule='05029' if recycle else '05030',used=used,capacity=capacity,remaining=max(0,capacity-used),limitations=['offline cache compatibility and matching not checked','all other device reservation counts still apply','no SC execution'])

def fault_completeness(*,result,unrecorded,count,capacity,max_query_count,data_requested):
 for value in (count,capacity,max_query_count):u32(value)
 if type(data_requested) is not bool:raise ValueError('explicit non-NULL output mode required')
 if type(unrecorded) is not bool or count>capacity or capacity>max_query_count:raise ValueError('invalid query metadata')
 if result not in ('VK_SUCCESS','VK_INCOMPLETE'):return 'QUERY_FAILED'
 if result=='VK_INCOMPLETE' or unrecorded:return 'INCOMPLETE_EVIDENCE'
 if not data_requested:return 'COUNT_QUERY_ONLY'
 return 'COMPLETE_FOR_RETURNED_QUERY_ONLY'
