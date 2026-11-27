"""Fixed independent raw gates for four authored resource families.
The checks are deliberately explicit copies of the family contracts, not code
loaded from result data. Entry authenticates this file and rule modules first.
"""
import hashlib,json,pathlib,uuid,struct,math,types,importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[1]
FAMILIES=('device_address','ray_query','robust_buffer','headless_wsi')
RULES={x:x+'19' for x in FAMILIES}
STATUSES={'device_address':'BOUNDED_PHYSICAL_STORAGE_ADDRESS_PASS','ray_query':'BOUNDED_BLAS_TLAS_RAY_QUERY_PASS','robust_buffer':'BOUNDED_ROBUST2_BUFFER_PASS','headless_wsi':'BOUNDED_HEADLESS_WSI_PASS'}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(x,m):
 if not x:raise ValueError(m)
def load_rule(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def safe_file(base,relative):
 p=pathlib.PurePosixPath(relative);require(not p.is_absolute() and '..' not in p.parts and str(p)==relative,'artifact path escape');target=base.joinpath(*p.parts)
 require(target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(base.resolve()),'missing/symlink artifact')
 for parent in target.parents:
  if parent==base:break
  require(not parent.is_symlink(),'symlink ancestor')
 return target
def log_record(scene,label,record):
 require(type(record['exit_code']) is int,'exit type')
 for stream in ('stdout','stderr'):require(record[stream+'_sha256']==sha(safe_file(scene,label+'.'+stream)),'log digest binding '+label)
def context(scene,t,saved):
 layer=json.loads(pathlib.Path(t['layer_path']).joinpath('VkLayer_khronos_validation.json').read_text())['layer']
 def execute(label,argv,expected=0):
  c=saved['cases'][label];log_record(scene,label,c);require(c['exit_code']==expected,'case exit')
  stdout=safe_file(scene,label+'.stdout').read_bytes();stderr=safe_file(scene,label+'.stderr').read_bytes();require([json.loads(x) for x in stdout.decode().splitlines()]==c['records'],'raw/report records mismatch')
  return types.SimpleNamespace(stdout=stdout,stderr=stderr),{'exit_code':expected,'stdout_sha256':sha(scene/(label+'.stdout')),'stderr_sha256':sha(scene/(label+'.stderr'))}
 return layer,execute

def verify_device_address(scene,t,saved):
 rules=load_rule('device_address19');layer,execute=context(scene,t,saved);report={'cases':{}};exe=scene/'probe';spv=scene/'compute.spv'
 inventory=json.loads(safe_file(scene,'inventory.stdout').read_text())
 require(inventory==saved['capability_inventory']['capabilities'],'inventory raw mismatch')
 for mode,code in [('good',0),('wrong-output',6),('missing-usage',0)]:
  r,logs=execute(mode,[exe,mode,spv],code);records=[json.loads(x) for x in r.stdout.decode().splitlines()];neg=mode=='missing-usage';order=['identity','features','buffer']+(['negative'] if neg else ['buffer','buffer','table','dispatch','readback','readback','oracle'])+['final'];require([x['kind'] for x in records]==order,'record lifecycle');by={}
  for x in records:by.setdefault(x['kind'],[]).append(x)
  ident=by['identity'][0];f=by['features'][0];fin=by['final'][0];require(ident['deviceType']==4 and ident['apiVersion']>>29==0 and ident['apiVersion']>=4202496 and ident['queueFlags']&2,'CPU scope');require(all(ident[k]==inventory[k] for k in ('deviceType','apiVersion','vendorID','deviceID','driverVersion')) and any(q['index']==ident['queueFamily'] and q['flags']==ident['queueFlags'] and q['count']>0 for q in inventory['queues']),'same inventory CPU identity');require(ident['layerSpec']==4210997 and ident['layerImplementation']==int(layer['implementation_version']),'layer identity');require(all(f[k]==1 for k in ('bdaSupported','int64Supported','bdaEnabled','int64Enabled')) and min(f[k] for k in ('maxLocalX','maxInvocations','maxGroupX','maxPushConstants'))>=8,'features/limits');ids=['VUID-VkBufferDeviceAddressInfo-buffer-02601'] if neg else [];require(r.stderr.decode().splitlines()==['address-query '+v for v in ids],'exact diagnostics');require(fin=={'kind':'final','submitted':not neg,'fenceCompleted':not neg,'errors':len(ids),'rc':code},'completion');admissions=[];ranges=[];buffers=by['buffer'];require([b['ordinal'] for b in buffers]==([0] if neg else [0,1,2]),'allocations')
  for i,b in enumerate(buffers):
   require(b['size']==(16 if i==2 else 272) and b['requirementsSize']>=b['size'] and b['requirementsAlignment']>0 and b['bindOffset']==0 and b['bindOffset']%b['requirementsAlignment']==0 and b['memoryFlags']&6==6 and b['memoryTypeBits']&(1<<b['memoryTypeIndex']) and b['live'] is True and b['generation']==0,'actual coherent allocation');ad=rules.admit(supported=bool(f['bdaSupported']),enabled=bool(f['bdaEnabled']),shader_int64_enabled=bool(f['int64Enabled']),usage=b['usage'],allocation_flags=b['allocationFlags'],bound=b['bound'],api_version=ident['apiVersion']);require(ad['status']==('MISSING_ADDRESS_USAGE' if neg else 'BDA_PREREQUISITES_WITHIN_SCOPE'),'address prerequisites');admissions.append(ad)
   if not neg:
    require(b['address']%b['requirementsAlignment']==0,'device address requirements alignment')
    rr=rules.validate_range(base=b['address'],size=b['size'],address=b['address'],length=16 if i==2 else 256,alignment=16,live=b['live'],retired=False);require(rr['status']=='ADDRESS_WITHIN_KNOWN_LIVE_BUFFER','address range');ranges.append(rr)
  if neg:require(by['negative']==[{'kind':'negative','addressConsumed':False,'returnedAddress':0}],'safe query rejected')
  else:
   require(all(a['address']+a['size']<=b['address'] or b['address']+b['size']<=a['address'] for i,a in enumerate(buffers) for b in buffers[i+1:]),'independent pointer ranges');table=by['table'][0];require(table=={'kind':'table','tableAddress':buffers[2]['address'],'sourceAddress':buffers[0]['address'],'outputAddress':buffers[1]['address'],'sourceOffset':0,'outputOffset':8,'alignment':16,'count':64},'pointer chain');d=by['dispatch'][0];require(d=={'kind':'dispatch','groups':[8,1,1],'pushAddress':table['tableAddress'],'pushSize':8,'beforeAccess':[16384,96],'afterAccess':[64,8192],'beforeStages':[16384,2048],'afterStages':[2048,16384]},'actual pointer dispatch dependency');require(rules.retire(submitted=fin['submitted'],write_visible=d['afterAccess']==[64,8192],fence_complete=fin['fenceCompleted'])['status']=='BOUNDED_READBACK_READY','retirement');readbacks=by['readback'];require([x['ordinal'] for x in readbacks]==[0,1],'readback order');source=[17+i*7 for i in range(68)];output=[source[i]*3+i for i in range(64)]+[0xc0ffee00+i for i in range(64,68)];require(readbacks[0]['values']==source and readbacks[1]['values']==output,'independent full output+guards');o=by['oracle'][0];require(o=={'kind':'oracle','expectedAddend':1 if mode=='wrong-output' else 0,'matched':mode!='wrong-output','guardsIntact':True,'tableValues':[buffers[0]['address'],buffers[1]['address']]},'real wrong oracle and table integrity')
  report['cases'][mode]={'records':records,'admissions':admissions,'ranges':ranges,'diagnostics':ids,**logs}
 require(report['cases']==saved['cases'],'independent family report differs')
 return report['cases']

def verify_ray_query(scene,t,saved):
 rules=load_rule('ray_query19');layer,execute=context(scene,t,saved);report={'cases':{}};exe=scene/'probe';spv=scene/'compute.spv'
 for mode,code in [('good',0),('wrong-output',6),('offset',0)]:
  r,logs=execute(mode,[exe,mode,spv],code);records=[json.loads(x) for x in r.stdout.decode().splitlines()];neg=mode=='offset';by={}
  for x in records:by.setdefault(x['kind'],[]).append(x)
  def one(k):require(len(by.get(k,[]))==1,'singleton '+k);return by[k][0]
  expected_order=['identity','features','buffer','buffer','buffer','vertices','geometry','build-config','buffer','buffer']+(['negative'] if neg else ['instance','as','build-config','buffer','buffer','as','descriptor','dependency','dependency','rays','dependency','readback'])+['final'];require([x['kind'] for x in records]==expected_order,'complete ordered record cohort');ident=one('identity');f=one('features');fin=one('final');require(ident['deviceType']==4 and ident['apiVersion']>>29==0 and ident['apiVersion']>=4202496 and ident['queueFlags']&2,'CPU scope');require(ident['layerSpec']==4210997 and ident['layerImplementation']==int(layer['implementation_version']),'layer identity');require(f['extensionsFound']==f['extensionsEnabled']==3 and all(f[k]==1 for k in ('bdaSupported','asSupported','raySupported','bdaEnabled','asEnabled','rayEnabled')),'features');require(f['vertexFormatFeatures']&0x20000000 and min(f['maxPrimitiveCount'],f['maxGeometryCount'],f['maxInstanceCount'])>=1,'AS capabilities')
  buffers=by['buffer'];require([x['ordinal'] for x in buffers]==([0,1,2,3,5] if neg else [0,1,2,3,5,4,6]),'buffer order');buf={x['ordinal']:x for x in buffers}
  for i,b in buf.items():
   usage=655360 if i<2 else 32 if i==2 else 1179648 if i<5 else 131104
   require(b['usage']==usage and b['allocationFlags']==(0 if i==2 else 2) and b['memoryFlags']&6==6 and b['memoryTypeBits']&(1<<b['memoryTypeIndex']) and b['requirementsSize']>=b['size'],'actual buffer capabilities')
   require((b['address']>0)==(i!=2),'BDA')
  require([buf[i]['size'] for i in (0,1,2)]==[36,64,32],'input/output sizes');require(by['build-config']==[{'kind':'build-config','index':i,'mode':0,'flags':4,'geometryCount':1,'primitiveCount':1} for i in range(1 if neg else 2)],'build configuration');require(buf[0]['address']%4==0 and buf[1]['address']%16==0,'build input BDA alignment');addresses=[(b['address'],b['address']+b['size']) for b in buffers if b['address']];require(all(e<=a or z<=s for i,(s,e) in enumerate(addresses) for a,z in addresses[i+1:]),'independent BDA ranges');require(one('vertices')['values']==[-1,-1,0,1,-1,0,0,1,0],'actual triangle');geo=one('geometry');require(geo=={'kind':'geometry','vertexFormat':106,'vertexStride':12,'maxVertex':2,'indexType':1000165000,'opaque':1,'vertexAddress':buf[0]['address'],'instanceAddress':buf[1]['address']},'geometry')
  ids=['VUID-VkAccelerationStructureCreateInfoKHR-offset-03734'] if neg else [];require(r.stderr.decode().splitlines()==['as-create '+i for i in ids],'exact diagnostics');require(fin=={'kind':'final','submitted':not neg,'fenceCompleted':not neg,'errors':len(ids),'rc':code},'completed cleanup');admissions=[];oracle=[]
  if neg:
   n=one('negative');require(n['result']==-1000011001 and n['offset']==1 and n['bufferSize']==buf[3]['size'],'abort');a0=rules.create(offset=n['offset'],size=n['size'],buffer_size=n['bufferSize'],storage_usage=True);require(a0['vuids']==ids,'create rejection');admissions.append(a0);require(not any(k in by for k in ('as','instance','readback','dependency','rays')),'no invalid handle consumed')
  else:
   require(len(by['as'])==2 and [x['index'] for x in by['as']]==[0,1],'AS order');require(by['as'][0]['type']==1 and by['as'][1]['type']==0,'BLAS TLAS')
   for i,x in enumerate(by['as']):
    require(x['scratchRawAddress']==buf[5+i]['address'] and x['scratchBufferSize']==buf[5+i]['size'] and x['storageSize']==buf[3+i]['size'] and x['asAddress']>0,'AS allocation association');c0=rules.create(offset=x['createOffset'],size=x['buildSize'],buffer_size=x['storageSize'],storage_usage=bool(buf[3+i]['usage']&1048576));a0=rules.scratch(address=x['scratchAddress'],buffer_address=x['scratchRawAddress'],buffer_size=x['scratchBufferSize'],required_size=x['scratchSize'],alignment=f['scratchAlignment'],storage_usage=bool(buf[5+i]['usage']&32),bda_usage=bool(buf[5+i]['usage']&131072));require(c0['status']=='CREATE_WITHIN_SCOPE' and a0['status']=='SCRATCH_WITHIN_SCOPE','AS admission');admissions.append({'create':c0,'scratch':a0})
   require(one('descriptor')=={'kind':'descriptor','asOrdinal':1,'asBinding':0,'asCount':1,'asType':1000150000,'outputBinding':1,'outputCount':1,'outputType':7,'outputRange':32},'descriptor configuration');require(one('instance')=={'kind':'instance','customIndex':7,'mask':255,'blasReference':by['as'][0]['asAddress'],'transform':[1,0,0,0,0,1,0,0,0,0,1,0]},'instance reference');deps=by['dependency'];require(deps==[{'kind':'dependency','index':i,'srcStage':s,'dstStage':d,'srcAccess':a,'dstAccess':b} for i,(s,d,a,b) in enumerate([(33554432,33554432,4194304,2097152),(33554432,2048,4194304,2097152),(2048,16384,64,8192)])],'build/query/host dependencies');rays=one('rays');require(rays['origins']==[[0,0,1],[3,0,1]] and rays['direction']==[0,0,-1] and rays['tmin']==0.1 and rays['tmax']==10 and rays['groups']==[2,1,1] and rays['maxGroupX']>=2 and rays['maxInvocations']>=1 and rays['maxPushConstants']>=32,'actual ray inputs');expected=[]
   for origin in rays['origins']:
    hit=rules.triangle_reference(origin,rays['direction'],rays['tmin'],rays['tmax']);oracle.append(hit)
    expected.extend([1,hit['customIndex'],struct.unpack('<I',struct.pack('<f',hit['t']))[0],hit['primitive']] if hit['hit'] else [0,0xffffffff,0,0xffffffff])
   actual=one('readback')['values'];require(len(actual)==8 and all(type(v) is int and 0<=v<=0xffffffff for v in actual),'result words');actual_t=struct.unpack('<f',struct.pack('<I',actual[2]))[0];require(all(actual[i]==expected[i] for i in (0,1,3,4,5,6,7)) and math.isfinite(actual_t) and abs(actual_t-oracle[0]['t'])<=1e-5 and one('readback')['expectedHit']==(0 if mode=='wrong-output' else 1),'independent geometry oracle')
  report['cases'][mode]={'records':records,'admissions':admissions,'cpu_oracle':oracle,'diagnostics':ids,**logs}
 require(report['cases']==saved['cases'],'independent family report differs')
 return report['cases']

def verify_robust_buffer(scene,t,saved):
 rules=load_rule('robust_buffer19');layer,execute=context(scene,t,saved);report={'cases':{}};exe=scene/'probe';spv=scene/'compute.spv'
 for mode,code in [('good',0),('wrong-output',6),('null-disabled',0)]:
  r,logs=execute(mode,[exe,mode,spv],code);records=[json.loads(x) for x in r.stdout.decode().splitlines()];neg=mode=='null-disabled';expectedk=['identity','features','allocation','allocation','contract']+([] if neg else ['pipeline','dispatch','dependency','source-readback','readback'])+['final'];require([x['kind'] for x in records]==expectedk,'record order');single={x['kind']:x for x in records if x['kind']!='allocation'};ident=single['identity'];f=single['features'];c=single['contract'];final=single['final'];require(ident['deviceType']==4 and ident['apiVersion']>>29==0 and ident['apiVersion']>=4198400 and ident['queueFlags']&2,'CPU identity');require(ident['layerSpec']==4210997 and ident['layerImplementation']==int(layer['implementation_version']),'actual layer');alloc=[x for x in records if x['kind']=='allocation'];require([x['index'] for x in alloc]==[0,1] and [x['size'] for x in alloc]==[f['sourceSize'],16],'independent allocations');require(all(x['memoryFlags']&6==6 and x['memoryTypeBits']&(1<<x['memoryTypeIndex']) and x['requirementsSize']>=x['size'] for x in alloc),'coherent types');require(all(f[k]==1 for k in ('extensionSupported','coreSupported','buffer2Supported','nullSupported','coreEnabled','buffer2Enabled')) and f['nullEnabled']==(0 if neg else 1),'supported enabled')
  update=rules.null_update(enabled=bool(f['nullEnabled']),is_null=True,offset=c['nullOffset'],whole_size=c['nullWholeSize']);ids=['VUID-VkDescriptorBufferInfo-buffer-02998'] if neg else [];require(update['vuids']==ids,'update admission');require(r.stderr.decode().splitlines()==['descriptor-update '+v for v in ids],'exact diagnostics');require(final=={'kind':'final','submitted':not neg,'fenceCompleted':not neg,'errors':len(ids),'rc':code},'completion')
  admission=None
  if not neg:
   m={k:bool(f[k]) for k in ('extensionSupported','coreSupported','coreEnabled','nullSupported','nullEnabled')};m.update(extensionEnabled=c['extensionEnabled'],robust2Supported=bool(f['buffer2Supported']),robust2Enabled=bool(f['buffer2Enabled']),ordinarySSBO=True,pipelineOverrideAbsent=single['pipeline']['pipelineOverrideAbsent'],storageAlignment=f['alignment'],descriptorRange=f['range'],sourceBufferSize=f['sourceSize'],sourceOffset=c['sourceOffset'],maxStorageRange=c['maxStorageRange'],maxStageStorageBuffers=c['maxStageStorageBuffers'],maxSetStorageBuffers=c['maxSetStorageBuffers'],readIndex=f['oobReadIndex'],writeIndex=f['oobWriteIndex'],outputRange=c['outputRange']);admission=rules.admit(m);require(admission['status']=='ROBUST2_BUFFER_WITHIN_SCOPE','access admission');require(single['dependency']=={'kind':'dependency','srcStage':2048,'dstStage':16384,'srcAccess':64,'dstAccess':8192},'host dependency');d=single['dispatch'];require(d['pushN']==f['range']//4 and d['pushSize']==4 and d['groups']==[1,1,1] and min(d['maxInvocations'],d['maxLocalX'],d['maxGroupX'])>=1 and d['maxPushConstantSize']>=4,'dispatch and push bounds');expected=[100,100+f['range']//4-1,0,0];oracle_expected=[*expected];oracle_expected[2]=1 if mode=='wrong-output' else 0;require(single['readback']['output']==expected and single['readback']['expected']==oracle_expected and single['readback']['fullSourceUnchanged'] is True,'actual output');require(single['source-readback']['values']==list(range(100,100+f['sourceSize']//4)),'full guard readback')
  report['cases'][mode]={'records':records,'null_admission':update,'access_admission':admission,'diagnostics':ids,**logs}
 require(report['cases']==saved['cases'],'independent family report differs')
 return report['cases']

def verify_headless_wsi(scene,t,saved):
 rules=load_rule('headless_wsi19');layer,execute=context(scene,t,saved);report={'cases':{}};exe=scene/'probe';spv=scene/'compute.spv'
 for mode,code in [('good',0),('wrong-output',6),('invalid-acquire',0)]:
  r,logs=execute(mode,[exe,mode],code);records=[json.loads(x) for x in r.stdout.decode().splitlines()];neg=mode=='invalid-acquire';order=['identity','readback-memory','formats','modes','image-format','generation']+(['negative'] if neg else ['frame','frame','formats','modes','image-format','generation','retirement','frame','frame','retirement'])+['final'];require([x['kind'] for x in records]==order,'ordered event lifecycle');by={}
  for x in records:by.setdefault(x['kind'],[]).append(x)
  ident=by['identity'][0];require(ident['deviceType']==4 and ident['apiVersion']>>29==0 and ident['apiVersion']>=4198400 and ident['queueFlags']&1 and ident['maintenanceSupported']==ident['maintenanceEnabled']==1 and ident['instanceExtensionsEnabled']==5 and ident['deviceExtensionsEnabled']==2,'CPU maintenance features');require(ident['layerSpec']==4210997 and ident['layerImplementation']==int(layer['implementation_version']),'actual layer');mem=by['readback-memory'][0];require(mem['bufferSize']==128 and mem['requirementsSize']>=128 and mem['memoryFlags']&6==6 and mem['memoryTypeBits']&(1<<mem['memoryTypeIndex']),'coherent memory');admissions=[]
  for i,g in enumerate(by['generation']):
   ip=by['image-format'][i];require(ip['generation']==i and ip['format']==g['format'] and ip['usage']==3 and ip['maxExtent'][0]>=g['width'] and ip['maxExtent'][1]>=g['height'] and ip['maxArrayLayers']>=1 and ip['sampleCounts']&1,'actual format capabilities');require(g['generation']==i and g['width']==(4 if i==0 else 8) and g['height']==4 and g['oldSwapchainPassed']==(i==1),'recreation');m={'minImages':g['minCount'],'maxImages':g['maxCount'],'requestedImages':g['requestedImages'],'usage':g['usage'],'supportedUsage':g['supportedUsage'],'presentMode':g['presentMode'],'format':g['format'],'colorSpace':g['colorSpace'],'selectedTransform':g['transform'],'supportedTransforms':g['supportedTransforms'],'selectedCompositeAlpha':g['compositeAlpha'],'supportedCompositeAlpha':g['supportedCompositeAlpha'],'maxLayers':g['maxLayers'],'extent':[g['width'],g['height']],'minExtent':g['minExtent'],'maxExtent':g['maxExtent'],'currentExtent':g['currentExtent'],'presentModes':by['modes'][i]['values'],'formats':by['formats'][i]['values'],'presentSupported':ident['presentSupported'],'swapchainEnabled':ident['swapchainEnabled'],'maintenanceSupported':bool(ident['maintenanceSupported']),'maintenanceEnabled':bool(ident['maintenanceEnabled'])};ad=rules.admit(m);require(ad['status']=='HEADLESS_WSI_WITHIN_SCOPE' and g['imageCount']>=g['requestedImages'],'WSI admission');admissions.append(ad)
  ids=['VUID-vkAcquireNextImageKHR-semaphore-01780'] if neg else [];require(r.stderr.decode().splitlines()==['invalid-acquire '+x for x in ids],'exact diagnostics');require(by['final']==[{'kind':'final','frames':0 if neg else 4,'errors':len(ids),'rc':code}],'final')
  if neg:require(by['negative']==[{'kind':'negative','result':-1000011001,'outputIndexConsumed':False}],'safe invalid acquire')
  else:
   require([(x['generation'],x['frame']) for x in by['frame']]==[(0,0),(0,1),(1,0),(1,1)],'four frames');seen=[set(),set()]
   for f in by['frame']:
    gen=f['generation'];j=f['frame'];g=by['generation'][gen];idx=f['imageIndex'];require(0<=idx<g['imageCount'] and rules.acquired(f['acquireResult'])['usable_image'],'acquired image');require(f['oldLayout']==(1000001002 if idx in seen[gen] else 0),'image layout history');seen[gen].add(idx);require(f['presentResult'] in (0,1000001003) and f['individualResult'] in (0,1000001003),'present results');ret=rules.retirement(generation=gen,current_generation=gen,render_fence=f['renderFenceCompleted'],present_fence=f['presentFenceCompleted'],queue_idle=f['queueIdle']);require(ret['status']=='SERIAL_PRESENT_RETIRED' and f['presentFenceAttached'] is True and f['renderWaitResult']==f['presentWaitResult']==0,'explicit presentation retirement');require(f['acquireWaitStage']==4096 and f['hostSrcAccess']==4096 and f['hostDstAccess']==8192 and f['endLayout']==1000001002,'dependency facts');rgba=[0 if j else 1,1 if gen else 0,1 if j else 0,1];require(f['rgba']==rgba and f['oracleInvertFirstByte']==(mode=='wrong-output'),'frame colors');pixel=[v*255 for v in rgba];pixel=pixel if g['format']==37 else [pixel[2],pixel[1],pixel[0],pixel[3]];require(f['normalExpectedBytes']==pixel and f['oracleExpectedFirstByte']==(255-pixel[0] if mode=='wrong-output' else pixel[0]),'actual oracle expectations');require(f['pixels']==pixel*(g['width']*g['height']),'all pixels independently decoded');require(mode!='wrong-output' or f['pixels'][0]!=255-pixel[0],'wrong oracle rejects')
   require(by['retirement']==[{'kind':'retirement','generation':i,'presentFencesCompleted':2,'destroyedAfterReplacement':i==0} for i in (0,1)],'generation retirement')
  report['cases'][mode]={'records':records,'admissions':admissions,'diagnostics':ids,**logs}
 require(report['cases']==saved['cases'],'independent family report differs')
 return report['cases']

def inspect_spirv(text):
 require('OpExecutionMode %main LocalSize 1 1 1' in text and 'OpAtomic' not in text,'shader execution scope')
 for name,b in [('src',0),('dst',1),('nil',2)]:
  require(f'OpDecorate %{name} Binding {b}' in text and f'OpDecorate %{name} DescriptorSet 0' in text,'shader descriptor identity')
 require('OpMemberDecorate %Params 0 Offset 0' in text,'push offset')
 pointers={};loads=[];stores=[]
 for line_no,line in enumerate(text.splitlines()):
  t=line.split()
  if len(t)>5 and t[1:3]==['=','OpAccessChain']:pointers[t[0]]=t[4]
  if len(t)==5 and t[1:3]==['=','OpLoad'] and pointers.get(t[4]) in ('%src','%nil'):loads.append((line_no,pointers[t[4]]))
  if len(t)==3 and t[0]=='OpStore' and pointers.get(t[1]) in ('%src','%nil'):stores.append((line_no,pointers[t[1]]))
 require([b for _,b in loads]==['%src','%src','%src','%nil'] and [b for _,b in stores]==['%src','%nil'] and max(i for i,_ in loads)<min(i for i,_ in stores),'protected reads precede both writes')
 return {'localSize':[1,1,1],'atomicInstructions':0,'protected_loads':loads,'protected_stores':stores,'scope':'Bounded disassembly structure check; not general SPIR-V semantic proof.'}
def verify_shader_structure(family,text):
 if family=='robust_buffer':return inspect_spirv(text)
 required={'device_address':('OpCapability PhysicalStorageBufferAddresses','OpMemoryModel PhysicalStorageBuffer64 GLSL450','OpCapability Int64','OpExecutionMode %main LocalSize 8 1 1','OpMemberDecorate %PointerTable 0 Offset 0','OpMemberDecorate %PointerTable 1 Offset 8','OpConvertUToPtr','Aligned 16','Aligned 8','Aligned 4','OpDecorate %_runtimearr_uint ArrayStride 4'),'ray_query':('OpCapability RayQueryKHR','OpRayQueryInitializeKHR','OpRayQueryProceedKHR','OpRayQueryGetIntersectionTypeKHR','OpRayQueryGetIntersectionTKHR','OpRayQueryGetIntersectionPrimitiveIndexKHR','OpExecutionMode %main LocalSize 1 1 1')}
 require(family in required and all(x in text for x in required[family]),'shader bounded structure')
def verify_normative(src,path,saved):
 require(sha(path)=='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7','fixed normative cohort');vu=json.loads(pathlib.Path(path).read_text());norm=json.loads((src/'normative.json').read_text());require(norm['source_sha256']==sha(path) and norm['version']==vu['version info']==saved['spec_version'],'normative version')
 for e in norm['entries']:require({k:v for k,v in e.items() if k not in ('owner','condition')} in vu['validation'][e['owner']][e['condition']],'normative exact entry')
def verify_family(family,scene,t):
 require(family in FAMILIES,'unknown family');scene=pathlib.Path(scene);saved=json.loads(safe_file(scene,'summary.json').read_text());require(saved['status']==STATUSES[family],'family status');require(str(uuid.UUID(saved['run_id']))==saved['run_id'],'child run UUID')
 case_names={'device_address':{'good','wrong-output','missing-usage'},'ray_query':{'good','wrong-output','offset'},'robust_buffer':{'good','wrong-output','null-disabled'},'headless_wsi':{'good','wrong-output','invalid-acquire'}}[family];require(set(saved['cases'])==case_names,'missing/extra case')
 src=ROOT/'cases19'/family;verify_normative(src,t['validusage'],saved)
 for key,path in {'source_sha256':src/'probe.c','runner_sha256':src/'run.py','rules_sha256':ROOT/'tools'/(family+'19.py'),'normative_sha256':src/'normative.json','loader_sha256':pathlib.Path(t['loader']),'icd_manifest_sha256':pathlib.Path(t['icd']),'layer_manifest_sha256':pathlib.Path(t['layer_path'])/'VkLayer_khronos_validation.json','spec_sha256':pathlib.Path(t['validusage'])}.items():require(saved[key]==sha(path),'source/tool cohort '+key)
 require(saved['binary_sha256']==sha(safe_file(scene,'probe')),'probe binary');require(saved['spec_version']==json.loads(pathlib.Path(t['validusage']).read_text())['version info'],'spec identity');log_record(scene,'build',saved['build']);require(saved['build']['exit_code']==0,'compile exit')
 if family!='headless_wsi':
  verify_shader_structure(family,safe_file(scene,'compute.spvasm').read_text())
  for key,path in {'shader_sha256':src/'compute.comp','spirv_sha256':safe_file(scene,'compute.spv'),'disassembly_sha256':safe_file(scene,'compute.spvasm')}.items():require(saved[key]==sha(path),'shader artifact binding')
  for field,label in [('compile','shader-compile'),('validate','shader-val'),('disassemble','shader-dis')]:log_record(scene,label,saved[field]);require(saved[field]['exit_code']==0,'shader tool exit')
  require(set(saved['tools'])=={'glslangValidator','spirv-val','spirv-dis'},'tool inventory')
  for name,tool in saved['tools'].items():require(tool['sha256']==sha(pathlib.Path(t['tools'])/name) and tool['version']==safe_file(scene,name+'-version.stdout').read_text(),'tool identity/version')
 if family=='device_address':
  inv=saved['capability_inventory'];require(inv['source_sha256']==sha(src/'capability_inventory.c') and inv['binary_sha256']==sha(safe_file(scene,'capability_inventory')),'inventory source/binary');log_record(scene,'inventory-build',inv['build']);log_record(scene,'inventory',inv['run']);require(inv['build']['exit_code']==inv['run']['exit_code']==0,'inventory execution');extensions=inv['capabilities']['extensions'];expected={'VK_KHR_video_queue','VK_KHR_video_decode_queue','VK_KHR_video_decode_h264','VK_KHR_video_decode_h265','VK_KHR_video_decode_av1','VK_KHR_video_encode_queue','VK_KHR_video_encode_h264','VK_KHR_video_encode_h265','VK_KHR_video_encode_av1','VK_EXT_subgroup_size_control','VK_KHR_cooperative_matrix','VK_NV_cooperative_matrix','VK_NV_optical_flow','VK_ARM_tensors','VK_ARM_data_graph','VK_KHR_buffer_device_address','VK_NV_cooperative_vector','VK_NV_memory_decompression','VK_EXT_memory_decompression','VK_NV_copy_memory_indirect','VK_QCOM_data_graph_model','VK_KHR_copy_memory_indirect'};require(set(extensions)==expected,'complete explicit extension inventory');require(all(type(v)is bool for v in extensions.values()),'inventory types');special=[x for x in extensions if x not in ('VK_EXT_subgroup_size_control','VK_KHR_buffer_device_address')];rule=load_rule('device_address19');require(rule.special_availability(extensions,special)==saved['special_availability'] and all(extensions[x] is False for x in special),'unavailable special families')
 globals()['verify_'+family](scene,t,saved)
 keys=('deviceType','apiVersion','vendorID','deviceID','driverVersion','layerSpec','layerImplementation');identities=[{k:row[k] for k in keys} for c in saved['cases'].values() for row in c['records'] if row['kind']=='identity'];require(len(identities)==3 and all(x==identities[0] for x in identities),'case identity changed')
 return {'family':family,'cpu_identity':identities[0],'run_id':saved['run_id'],'status':saved['status'],'summary_sha256':sha(scene/'summary.json'),'artifacts':{str(p.relative_to(scene)):sha(safe_file(scene,str(p.relative_to(scene)))) for p in scene.rglob('*') if p.is_file()}}
