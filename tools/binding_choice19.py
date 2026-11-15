"""Ordinary set vs KHR push descriptors: fixed two-generation output/call-count gate."""
import copy
from tools import upload_choice19 as common

def check(records,path,wrong=False):
 def need(c,s):
  if not c:raise ValueError(s)
 need(path in ('set','push') and type(wrong) is bool and type(records) is list and all(type(x) is dict for x in records),'schema')
 header=['identity','binding_config','allocation','allocation'];body=['generation','input','dependency','dispatch','dependency','readback','result']
 need([r.get('kind') for r in records]==header+body*2+['binding_cost'],'exact records')
 config=records[1];need(set(config)=={'kind','pushSupported','pushEnabled','maxPushDescriptors','layoutFlags','descriptorType','descriptorCount'},'config fields')
 need(type(config['pushSupported']) is bool and type(config['pushEnabled']) is bool and all(type(config[k]) is int and 0<=config[k]<2**32 for k in ('maxPushDescriptors','layoutFlags','descriptorType','descriptorCount')),'config types')
 need(config['pushEnabled'] is (path=='push') and config['layoutFlags']==(1 if path=='push' else 0) and config['descriptorType']==7 and config['descriptorCount']==2,'actual layout')
 if path=='push':need(config['pushSupported'] and config['maxPushDescriptors']>=2,'push capability and enablement')
 generations=[]
 for gen in range(2):
  part=records[4+7*gen:4+7*(gen+1)];need(part[0]==dict(kind='generation',index=gen,priorFenceCompleted=bool(gen)) and type(part[0]['index']) is int and type(part[0]['priorFenceCompleted']) is bool,'generation/fence ordering')
  inp=part[1]['values'];rb=part[-2];final=part[-1]
  need(inp==[7*i+3+100*gen for i in range(64)] and all(type(x) is int for x in inp),'actual complete input')
  need(rb['values']==[22*i+9+300*gen for i in range(64)] and all(type(x) is int for x in rb['values']),'independent generation output')
  need(type(rb['mismatches']) is int and rb['mismatches']==int(wrong and gen==1) and type(rb['oracleFirst']) is int and rb['oracleFirst']==9+300*gen+int(wrong and gen==1),'actual wrong reference')
  need(final['path']==path,'actual binding path')
  # Reuse the independently tested common coherent-buffer dependency/dispatch gate.
  # Project only already-checked arithmetic and path labels to its fixed workload;
  # raw original records remain untouched and are retained in the report.
  projected=copy.deepcopy([records[0],*records[2:4],*part[1:]])
  projected[3]['values']=[7*i+3 for i in range(64)]
  projected[-2]['values']=[22*i+9 for i in range(64)];projected[-2]['oracleFirst']=9+int(wrong and gen==1)
  projected[-1]['path']='direct'
  commoncheck=common.check(projected,'direct',wrong and gen==1)
  generations.append(dict(generation=gen,input=inp,output=rb['values'],requested_bytes=commoncheck['requested_bytes'],allocation_receipt=commoncheck['allocation_receipt']))
 cost=records[-1];expected=dict(kind='binding_cost',descriptorPoolCreates=0 if path=='push' else 1,descriptorSetAllocations=0 if path=='push' else 1,updateCalls=0 if path=='push' else 1,bindCalls=0 if path=='push' else 2,pushCalls=2 if path=='push' else 0,dispatches=2)
 need(cost==expected and all(type(v) is int for k,v in cost.items() if k!='kind'),'actual call counters')
 return dict(status='BINDING_PATH_VERIFIED',path=path,identity=records[0],config=config,generations=generations,cost=cost,limits='Two SSBO descriptors, sequential fence-retired dispatches; call counts not driver memory or performance; layouts are distinct, not declared compatible.')

def decide(traditional,push,max_set_allocations,performance_required=False):
 def out(s,selected=None,why=''):return dict(status=s,selected=selected,reason=why,rule_id='verified-binding-call-policy-v1',unmeasured=['GPU/full-frame performance','driver descriptor memory','dynamic indexing/bindless','descriptor buffers'],policy_scope='application-managed descriptor-set allocation count, not Vulkan hardware capacity')
 if type(max_set_allocations) is not int or not 0<=max_set_allocations<2**32 or type(performance_required) is not bool:return out('UNKNOWN')
 try:
  traditional=check(traditional,'set')
  push=check(push,'push') if push is not None else None
 except (ValueError,TypeError,KeyError):return out('UNKNOWN')
 if push is None and performance_required:return out('NEEDS_MEASUREMENT',None,'missing performance evidence; independently verified set is a possible fallback only if application budget allows')
 if push is None:return out('KEEP_BASELINE' if max_set_allocations>=1 else 'NO_ADMISSIBLE_PATH','set' if max_set_allocations>=1 else None,'push not observed/unsupported; no comparative performance inference')
 if type(push) is not dict or push.get('status')!='BINDING_PATH_VERIFIED' or push.get('path')!='push':return out('UNKNOWN')
 for record in (traditional,push):
  if type(record.get('identity')) is not dict or type(record.get('generations')) is not list or len(record['generations'])!=2:return out('UNKNOWN')
  for gen in record['generations']:
   if type(gen) is not dict or type(gen.get('output')) is not list or len(gen['output'])!=64 or any(type(x) is not int for x in gen['output']):return out('UNKNOWN')
 if traditional.get('identity')!=push.get('identity') or [g['output'] for g in traditional['generations']]!=[g['output'] for g in push['generations']]:return out('UNKNOWN')
 if performance_required:return out('NEEDS_MEASUREMENT',None,'call counts cannot prove frame-time benefit')
 return out('KEEP_BASELINE' if max_set_allocations>=1 else 'SELECT_ONLY_POLICY_ADMISSIBLE_PATH','set' if max_set_allocations>=1 else 'push','verified baseline preferred unless explicit application allocation-count policy excludes it')
