"""Bounded ordinary timestamp contract, not clock calibration or performance proof."""
import math
PREFIX='VUID-vkGetQueryPoolResults-'
def integer(x, minimum=0):
 if type(x) is not int or x<minimum: raise ValueError('integer required')
 return x

def layout(*,width,count,stride,data_size,availability,partial=False):
 if width not in (32,64) or type(width) is not int:raise ValueError('width')
 integer(count,1);integer(stride);integer(data_size,1)
 if type(availability) is not bool or type(partial) is not bool:raise ValueError('boolean flags')
 unit=width//8;record=unit*(2 if availability else 1);v=[]
 if partial:v.append(PREFIX+'queryType-09439')
 if count>1 and stride==0:v.append(PREFIX+'queryCount-09438')
 if stride%unit:v.append(PREFIX+('flags-00815' if width==64 else 'flags-02828'))
 if availability and stride<record:v.append(PREFIX+'stride-08993')
 if data_size<(count-1)*stride+record:v.append(PREFIX+'dataSize-00817')
 return {'status':'REJECTED' if v else 'LAYOUT_WITHIN_SCOPE','vuids':v,'required_bytes':(count-1)*stride+record,'limitation':'pData address alignment and accessible storage are separate caller obligations'}

def consume(*,identity,observation,valid_bits,period_ns,same_clock,upper_bound_ns,result_width):
 if valid_bits is None or period_ns is None:return {'status':'UNKNOWN','reason':'missing observed capability'}
 if type(result_width) is not int or result_width not in (32,64):raise ValueError('result width')
 if result_width!=64:return {'status':'UNKNOWN_32BIT_REPRESENTATION'}
 integer(valid_bits)
 if valid_bits==0:return {'status':'UNSUPPORTED','vuid':'VUID-vkCmdWriteTimestamp-timestampValidBits-00829'}
 if valid_bits>64:raise ValueError('valid bits')
 if isinstance(period_ns,bool) or not isinstance(period_ns,(int,float)) or not math.isfinite(period_ns) or period_ns<=0:raise ValueError('period')
 keys=('run','device','pool','queue','generation')
 for obj in (identity,observation):
  if not isinstance(obj,dict) or any(k not in obj for k in keys):raise ValueError('identity')
  for k in keys[:-1]:
   if not isinstance(obj[k],str) or not obj[k]:raise ValueError('identity')
  integer(obj['generation'])
 if any(identity[k]!=observation[k] for k in keys):return {'status':'STALE_OR_DIFFERENT_SCOPE'}
 if observation.get('reset_completed') is not True or observation.get('writes_completed') is not True:return {'status':'NOT_READY'}
 values=observation.get('values');available=observation.get('availability')
 if not isinstance(values,list) or len(values)!=2 or not isinstance(available,list) or len(available)!=2:raise ValueError('two results required')
 for x in values+available:
  integer(x)
  if x>(1<<64)-1:raise ValueError('result exceeds uint64')
 if any(x==0 for x in available):return {'status':'NOT_READY'}
 if same_clock is not True:return {'status':'UNKNOWN_CLOCK'}
 wrap=(1<<valid_bits)*period_ns
 if isinstance(upper_bound_ns,bool) or not isinstance(upper_bound_ns,(int,float)) or not math.isfinite(upper_bound_ns) or upper_bound_ns<0 or upper_bound_ns>=wrap:return {'status':'UNKNOWN_WRAP'}
 delta=(values[1]-values[0])&((1<<valid_bits)-1);ns=delta*period_ns
 if ns>upper_bound_ns:return {'status':'INCONSISTENT_BOUND'}
 return {'status':'BOUNDED_MODULAR_DELTA','ticks':delta,'nanoseconds':ns,'limitation':'caller-supplied same clock and independent elapsed bound; not calibrated hardware performance'}

def write_admission(*,valid_bits,pool_type,pool_count,query,reset_executed,already_written,stage_supported):
 if pool_type not in ('timestamp','occlusion','pipeline-statistics'):return {'status':'UNKNOWN','reason':'unclassified query type'}
 if valid_bits is None or reset_executed is None or already_written is None or stage_supported is None:return {'status':'UNKNOWN','reason':'missing observed capability/state'}
 integer(valid_bits);integer(pool_count,1);integer(query)
 if valid_bits>64:raise ValueError('valid bits')
 for x in (reset_executed,already_written,stage_supported):
  if type(x) is not bool:raise ValueError('explicit state facts required')
 vuids=[]
 if pool_type!='timestamp':vuids.append('VUID-vkCmdWriteTimestamp-queryPool-01416')
 if valid_bits==0:vuids.append('VUID-vkCmdWriteTimestamp-timestampValidBits-00829')
 if query>=pool_count:vuids.append('VUID-vkCmdWriteTimestamp-query-04904')
 if not reset_executed or already_written:vuids.append('VUID-vkCmdWriteTimestamp-None-00830')
 if not stage_supported:vuids.append('VUID-vkCmdWriteTimestamp-pipelineStage-04074')
 return {'status':'REJECTED' if vuids else 'WRITE_WITHIN_SCOPE','vuids':vuids,'limitation':'caller must independently establish reset execution, exclusive slot ownership, queue/stage support; recording reset alone is insufficient'}


def query_range(*,pool_count,first_query,count):
 if pool_count is None or first_query is None or count is None:return {'status':'UNKNOWN','reason':'missing range facts'}
 integer(pool_count,1);integer(first_query);integer(count)
 if count==0:return {'status':'UNKNOWN','reason':'zero count outside bounded family, no invented VUID'}
 v=[]
 if first_query>=pool_count:v.append(PREFIX+'firstQuery-09436')
 if first_query+count>pool_count:v.append(PREFIX+'firstQuery-09437')
 return {'status':'REJECTED' if v else 'RANGE_WITHIN_SCOPE','vuids':v}
