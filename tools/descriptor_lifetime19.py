"""Ordinary descriptor-set update planner, NOT queue completion detection.
Caller must supply independently observed command-buffer states and same-scope
references; timeline values without known submission coverage are insufficient.
"""
VALID={'initial','recording','executable','pending','invalid'}
def plan(*,binding_model,identity,references,inventory_complete,host_exclusive):
 if binding_model!='ordinary':return {'status':'OUT_OF_SCOPE','reason':'advanced binding flags require their own contracts'}
 keys=('run','device_id','set_id','device_generation','set_generation')
 if not isinstance(identity,dict) or any(identity.get(k) is None for k in keys):raise ValueError('scope identity required')
 if any(not isinstance(identity[k],str) or not identity[k] for k in ('run','device_id','set_id')):raise ValueError('nonempty object identity required')
 if any(type(identity[k]) is not int or identity[k]<0 for k in ('device_generation','set_generation')):raise ValueError('integer generation required')
 if not isinstance(references,list):raise ValueError('reference list required')
 if type(inventory_complete) is not bool or type(host_exclusive) is not bool:raise ValueError('explicit ownership/inventory facts required')
 if not host_exclusive:return {'status':'REJECTED_HOST_RACE','reason':'serialize ordinary descriptor host update'}
 if not inventory_complete:return {'status':'UNKNOWN','reason':'all referencing command buffers must be accounted for'}
 rerecord=[];pending=[]
 for ref in references:
  if not isinstance(ref,dict) or not ref.get('command_buffer'):raise ValueError('command-buffer reference required')
  if ref.get('state') not in VALID:raise ValueError('unknown command state')
  if any(type(ref.get(k)) is not type(identity[k]) or ref.get(k)!=identity[k] for k in keys):return {'status':'UNKNOWN','reason':'stale run/device/set scope'}
  if ref['state']=='pending':pending.append(ref['command_buffer'])
  elif ref['state'] in ('recording','executable'):rerecord.append(ref['command_buffer'])
 if pending:return {'status':'WAIT_RETIREMENT','pending':sorted(set(pending)),'vuid':'VUID-vkUpdateDescriptorSets-None-03047','reason':'observed pending use forbids ordinary update'}
 return {'status':'UPDATE_REQUIRES_RERECORD' if rerecord else 'UPDATE_WITHIN_SCOPE','rerecord':sorted(set(rerecord)),'limitations':['not permission to resubmit old executable command buffers','no GPU memory-content visibility proof','does not establish resource retirement on other queues or presentation']}
