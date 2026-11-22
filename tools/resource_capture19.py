"""Bounded two-slot capture validation. Logs are observations, not authenticated truth."""
import hashlib,json,math
from . import binding_choice19 as binding,memory_binding_contract19 as memory
SCOPE='traditional-two-ssbo-single-thread-single-queue-two-epochs'
OBLIGATIONS=('complete_single_thread_inventory','allocation_and_pipeline_validity','host_coherent_submission_scope')
def need(x,msg):
 if not x:raise ValueError(msg)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def strict_equal(a,b):return digest(a)==digest(b)
def references():return [dict(buffer=i,allocation=i,generation=1,access=('READ','WRITE')[i],binding=i,array_element=0,offset=0,size=256) for i in range(2)]
def bounded_tree(value,depth=0,counter=None):
 if counter is None:counter=[0]
 counter[0]+=1;need(depth<=20 and counter[0]<=20000,'bounded JSON depth/nodes')
 if type(value)is dict:
  need(all(type(k)is str for k in value),'JSON keys')
  for v in value.values():bounded_tree(v,depth+1,counter)
 elif type(value)is list:
  for v in value:bounded_tree(v,depth+1,counter)
 elif type(value)is float:need(math.isfinite(value),'finite JSON')
 else:need(value is None or type(value)in (str,int,bool),'JSON scalar')
def check_v2(trace):
 try:
  bounded_tree(trace);need(len(json.dumps(trace,allow_nan=False))<=1024*1024,'trace byte limit')
  need(type(trace)is dict and set(trace)=={'schema','scope','records','events','wrong','obligations'},'v2 schema')
  need(type(trace['schema'])is int and trace['schema']==2 and trace['scope']==SCOPE,'v2 scope')
  records,events=trace['records'],trace['events'];wrong=trace['wrong']
  need(type(wrong)is bool and type(events)is list and 0<len(events)<256,'bounded events')
  verified=binding.check(records,'set',wrong)
  need(all(type(e)is dict and type(e.get('seq'))is int and e['seq']==i for i,e in enumerate(events)),'event sequence missing/duplicate')
  events=[{k:v for k,v in e.items() if k!='seq'} for e in events];cursor=0
  def take(expected):
   nonlocal cursor
   need(cursor<len(events) and strict_equal(events[cursor],expected),'event/identity mismatch at '+str(cursor));cursor+=1
  def api(call):take(dict(op='api',call=call,result=0))
  def event(op,epoch,**kw):take(dict(op=op,epoch=epoch,**kw))
  event('capture_start',1)
  for call in ['vkEnumerateInstanceLayerProperties(&n,0)','vkCreateInstance(&ic,0,&in)','create(in,&dc,0,&msg)','vkEnumeratePhysicalDevices(in,&n,0)','vkEnumeratePhysicalDevices(in,&n,&physical)','vkEnumerateDeviceExtensionProperties(physical,0,&ec,0)','vkCreateDevice(physical,&di,0,&dev)']:api(call)
  alloc=[r for r in records if r['kind']=='allocation']
  for i,a in enumerate(alloc):
   api('vkCreateBuffer(dev,&bi,0,&buf[i])')
   take(dict(op='requirements',buffer=i,generation=1,size=a['requestedBytes'],alignment=a['requirementsAlignment'],type_bits=a['typeBits'],requires_dedicated=0))
   api('vkAllocateMemory(dev,&ai,0,&mem[i])');api('vkBindBufferMemory(dev,buf[i],mem[i],0)')
   take(dict(op='bind',buffer=i,allocation=i,generation=1,logical_size=a['logicalBytes'],allocation_size=a['requestedBytes'],memory_type=a['typeIndex'],offset=a['bindOffset']))
   f=dict(kind='buffer',resource_id='B'+str(i),ordinary_scope_proven=True,allocation_creation_valid=True,same_device=True,requirements_size=a['requestedBytes'],requirements_alignment=a['requirementsAlignment'],memory_type_bits=a['typeBits'],memory_type_index=a['typeIndex'],allocation_size=a['requestedBytes'],offset=a['bindOffset'],already_bound=False,requires_dedicated=False,prefers_dedicated=False,dedicated=None)
   need(memory.bind(f)['status']=='BIND_CONDITIONS_WITHIN_SCOPE','memory binding contract')
   api('vkMapMemory(dev,mem[i],0,256,0,&maps[i])');take(dict(op='host_write',buffer=i,allocation=i,resource_generation=1,content_epoch=0,offset=0,size=256,values=[0xdeadbeef]*64 if i else [j*7+3 for j in range(64)]))
  for call in ['vkCreateShaderModule(dev,&sci,0,&sm)','vkCreateDescriptorSetLayout(dev,&si,0,&sl)','vkCreatePipelineLayout(dev,&pli,0,&pl)','vkCreateComputePipelines(dev,0,1,&pci,0,&pipe)','vkCreateDescriptorPool(dev,&dpi,0,&dp)','vkAllocateDescriptorSets(dev,&sa,&set)']:api(call)
  take(dict(op='descriptor_update',set=0,bindings=[dict(binding=i,array_element=0,buffer=i,generation=1,offset=0,size=256) for i in range(2)]))
  for call in ['vkCreateCommandPool(dev,&cpi,0,&cp)','vkAllocateCommandBuffers(dev,&cai,&cmd)','vkCreateFence(dev,&fi,0,&fence)']:api(call)
  for epoch in range(2):
   if epoch:
    api('vkResetFences(dev,1,&fence)');api('vkResetCommandPool(dev,cp,0)')
   if epoch:
    for i in range(2):take(dict(op='host_write',buffer=i,allocation=i,resource_generation=1,content_epoch=epoch,offset=0,size=256,values=[0xdeadbeef]*64 if i else [j*7+3+100*epoch for j in range(64)]))
   api('vkBeginCommandBuffer(cmd,&begin)');event('begin_record',epoch)
   take(dict(op='record_use',cb=0,recording=epoch,set=0,references=references()))
   api('vkEndCommandBuffer(cmd)');event('end_record',epoch)
   api('vkQueueSubmit(queue,1,&sub,fence)')
   ids=dict(cb=0,fence=0,queue=0,submission=epoch,recording=epoch,buffers=[0,1],allocations=[0,1],resource_generations=[1,1])
   event('submit',epoch,**ids);api('vkWaitForFences(dev,1,&fence,VK_TRUE,10000000000ull)');event('complete',epoch,**ids);event('host_read',epoch,buffer=1,allocation=1,resource_generation=1,offset=0,size=256)
  for i in range(2):
   event('unmap',i);event('destroy_buffer',i);take(dict(op='free_allocation',allocation=i,generation=1))
   need(memory.free_obligations(dict(bound_object_count=0,all_submitted_uses_retired=True,host_accesses_completed=True,no_future_bound_resource_use=True,reference_inventory_complete=True))['status']=='FREE_LIFETIME_OBLIGATIONS_DECLARED','free obligation')
  take(dict(op='capture_end',rc=6 if wrong else 0));need(cursor==len(events),'extra events')
  obligations=trace['obligations'];need(type(obligations)is dict and set(obligations)==set(OBLIGATIONS),'obligation schema')
  need(all(v in ('CALLER_DECLARED','UNRESOLVED') for v in obligations.values()),'authority cannot be promoted')
  status='CONSISTENT_DECLARED_TRACE' if all(v=='CALLER_DECLARED' for v in obligations.values()) else 'OBLIGATIONS_NOT_ESTABLISHED'
  return dict(status=status,observations='BOUNDED_CAPTURE_AND_OUTPUT_RECOMPUTED',epochs=2,submissions=2,references_per_submission=2,resource_generations=[1,1],content_epochs=[0,1],wrong_oracle_rejected=wrong,identity=verified['identity'],authority=obligations,limitations=['Captured source-cohort observations, not authenticated or exhaustive Vulkan truth','No invented compute-to-compute barrier: prior fence then full coherent host rewrite then submission','Input HOST barrier is a fixture check, not universally required','No pending update/free or illegal GPU negative executed','No full L1/L2 or release promotion'])
 except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError) as e:return dict(status='REJECTED_DECLARED_TRACE',reason=str(e))
def adapt(records,events,wrong,obligations=None):
 return dict(schema=2,scope=SCOPE,records=records,events=events,wrong=wrong,obligations=obligations or {k:'UNRESOLVED' for k in OBLIGATIONS})
