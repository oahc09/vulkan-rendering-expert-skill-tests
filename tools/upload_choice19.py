"""Bounded actual-record verification and requested-allocation budget decision."""
def check(records,path,wrong=False):
 def need(c,s):
  if not c:raise ValueError(s)
 need(type(records) is list and all(type(x) is dict for x in records) and path in ('direct','staging'),'schema')
 need(type(wrong) is bool,'wrong flag type')
 for record in records:
  for key,value in record.items():
   if key in ('kind','path'):need(type(value) is str,'string field')
   elif key in ('mapped','submitted','fenceCompleted'):need(type(value) is bool,'boolean field')
   elif type(value) is list:need(all(type(x) is int and 0<=x<2**32 for x in value),'integer vector')
   else:need(type(value) is int and 0<=value<2**64,'integer scalar')
 staging=path=='staging';kinds=['identity']+['allocation']*(3 if staging else 2)+['input','dependency']+(['copy','dependency'] if staging else [])+['dispatch','dependency','readback','result']
 need([x.get('kind') for x in records]==kinds,'record sequence')
 ident=records[0];need(all(type(v) is int and 0<=v<2**32 for k,v in ident.items() if k!='kind'),'uint32 identity');need(all(type(ident.get(k)) is int for k in ('deviceType','api','queueFlags','layerSpec','layerImpl','vendor','device','driver','queue')),'identity types');need(ident['deviceType']==4 and ident['api']>>29==0 and ident['api']>=4198400 and ident['queueFlags']&2 and ident['layerSpec']==4210997 and ident['layerImpl']==1,'CPU/VVL scope')
 for k,minv in [('maxInvocations',64),('maxLocalX',64),('maxGroupX',1),('maxPerStageSSBO',2),('maxSetSSBO',2),('maxRange',256)]:need(type(ident[k]) is int and ident[k]>=minv,'actual limit')
 alloc=[r for r in records if r['kind']=='allocation'];need([x['index'] for x in alloc]==list(range(len(alloc))),'allocation IDs')
 for a in alloc:
  i=a['index'];need(all(type(a[k]) is int for k in ('logicalBytes','requestedBytes','requirementsAlignment','typeBits','typeIndex','flags','heapIndex','heapSize','heapFlags','usage','bindOffset')),'allocation numeric fields')
  need(a['logicalBytes']==256 and 256<=a['requestedBytes']<2**63 and 0<a['requirementsAlignment']<2**63 and a['bindOffset']==0 and 0<=a['typeIndex']<32 and a['typeBits']&(1<<a['typeIndex']),'memory requirements')
  need(0<=a['flags']<2**32 and 0<=a['typeBits']<2**32 and 0<=a['heapFlags']<2**32 and 0<=a['usage']<2**32,'uint32 masks');need(0<=a['heapIndex']<16 and a['heapSize']>=a['requestedBytes'],'heap metadata')
  local=staging and i==0;need((a['flags']&(1 if local else 6))==(1 if local else 6),'required memory flags')
  need(a['mapped'] is (not local) and a['usage']==([34,32,1] if staging else [32,32])[i],'actual path topology')
 inputrow=next(x for x in records if x['kind']=='input');need(inputrow['values']==[i*7+3 for i in range(64)] and all(type(x) is int for x in inputrow['values']),'actual full input')
 deps=[x for x in records if x['kind']=='dependency'];expected=[(2,16384,4096,16384,2048),(0,4096,2048,4096,32),(1,2048,16384,64,8192)] if staging else [(0,16384,2048,16384,32),(1,2048,16384,64,8192)]
 need([tuple(x[k] for k in ('bufferIndex','srcStage','dstStage','srcAccess','dstAccess')) for x in deps]==expected and all(x['size']==256 for x in deps),'actual scoped dependencies')
 if staging:need(next(x for x in records if x['kind']=='copy')==dict(kind='copy',src=2,dst=0,srcOffset=0,dstOffset=0,bytes=256),'actual copy')
 need(next(x for x in records if x['kind']=='dispatch')==dict(kind='dispatch',groups=[1,1,1],local=[64,1,1],inputBuffer=0,outputBuffer=1,descriptorRange=256),'same shader dispatch')
 rb=next(x for x in records if x['kind']=='readback');expectedout=[3*(7*i+3)+i for i in range(64)]
 need(rb['values']==expectedout and all(type(x) is int for x in rb['values']),'independent complete output oracle')
 need(rb['mismatches']==int(wrong) and rb['oracleFirst']==(10 if wrong else 9),'actual wrong reference comparison')
 final=records[-1];need(all(type(final.get(k)) is int for k in ('errors','rc','requestedBytesTotal','logicalBytesTotal','cpuSubmitWaitNs')),'result numeric types');need(final['path']==path and final['submitted'] is True and final['fenceCompleted'] is True and final['errors']==0 and final['rc']==(6 if wrong else 0),'completion')
 total=sum(x['requestedBytes'] for x in alloc);need(final['requestedBytesTotal']==total and final['logicalBytesTotal']==len(alloc)*256 and type(final['cpuSubmitWaitNs']) is int and 0<=final['cpuSubmitWaitNs']<2**63,'actual allocation/cost observation')
 return dict(status='BOUNDED_UPLOAD_PATH_VERIFIED',path=path,requested_bytes=total,logical_bytes=final['logicalBytesTotal'],output=expectedout,allocation_receipt=alloc,identity=ident,not_proven=['GPU performance','dedicated physical memory domains','noncoherent correctness','physical hardware performance'])

def decide(direct,staging,budget,require_performance=False):
 if type(budget) is not int or not 0<=budget<2**63 or type(require_performance) is not bool:return dict(status='UNKNOWN',selected=None)
 for x,p in ((direct,'direct'),(staging,'staging')):
  if type(x) is not dict or x.get('status')!='BOUNDED_UPLOAD_PATH_VERIFIED' or x.get('path')!=p or type(x.get('requested_bytes')) is not int or not 0<x['requested_bytes']<2**63 or type(x.get('identity')) is not dict or type(x.get('output')) is not list or len(x['output'])!=64 or any(type(v) is not int for v in x['output']):return dict(status='UNKNOWN',selected=None)
 if direct['output']!=staging['output'] or direct['identity']!=staging['identity']:return dict(status='UNKNOWN',selected=None)
 eligible=[x['path'] for x in (direct,staging) if x['requested_bytes']<=budget]
 if not eligible:return dict(status='NO_ADMISSIBLE_PATH',selected=None)
 if require_performance:return dict(status='NEEDS_MEASUREMENT',selected=None,fallback='direct' if 'direct' in eligible else None)
 selected='direct' if 'direct' in eligible else 'staging'
 return dict(status='KEEP_BASELINE' if selected=='direct' else 'SELECT_ONLY_BUDGET_ADMISSIBLE_PATH',selected=selected,rule_id='verified-upload-request-budget-v1',reason='actual simultaneous requested allocation budget only; not residency/performance',limitations=['Caller must independently validate complete raw records/source before decision; status strings are not authentication.','No physical memory, throughput or GPU latency superiority inferred.'],revisit_conditions=['source/device/driver/input/size change','budget or performance requirement change'])
