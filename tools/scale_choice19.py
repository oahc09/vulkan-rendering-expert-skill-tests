"""Fixed 16-candidate culling experiment. Direct draws are not optimal CPU batching."""
import copy
from tools import render_organization19 as common
MASK=[1,0,1,0,0,1,0,1,1,0,0,0,0,1,1,0]
def require(c,s):
 if not c:raise ValueError(s)
def reference(ids=None):
 ids={i for i,v in enumerate(MASK) if v} if ids is None else set(ids)
 return [common.reference()[i] if i in ids else [255,0,255,255] for i in range(16)]
def ints(value):
 if type(value)is dict:
  for k,v in value.items():
   if k not in ('kind','path'):ints(v)
 elif type(value)is list:
  for v in value:ints(v)
 else:require(type(value)is int and 0<=value<2**64,'exact uint field')
def check(rows,path,mode='good'):
 require(path in ('direct','indirect') and mode in ('good','wrong-output','limited-count') and not(path=='direct' and mode=='limited-count'),'mode')
 require(type(rows)is list and all(type(x)is dict for x in rows),'rows')
 kinds=[x.get('kind') for x in rows]
 expected=['identity','limits','image_allocation','buffer_allocation','scale_allocation','scale_allocation','binding_facts','scale_config','pipeline','image_dependency']+(['indirect_dependency'] if path=='indirect' else [])+['manifest','image_dependency','host_dependency']+(['argument_retirement_dependency'] if path=='indirect' else [])+['commands','execution','organization','final']
 require(kinds==expected,'record sequence')
 r={x['kind']:x for x in rows};bf=r['binding_facts'];ints(bf);require(all(bf[k]==v for k,v in dict(inputOffset=0,inputRange=64,outputOffset=0,outputRange=272,inputIsMask=1,outputIsCommands=1,countAndCommandsSameBuffer=1,dispatch=[1 if path=='indirect' else 0,1,1]).items()) and all(bf[k]>=1 for k in ('maxComputeInvocations','maxComputeSizeX','maxComputeCountX')),'compute binding facts');c=r['scale_config'];ints(c)
 require(c['visibility']==MASK and c['candidates']==16 and c['visibleCount']==7 and c['maxDrawCount']==(6 if mode=='limited-count' else 16) and c['stride']==16 and c['countOffset']==256,'workload/count bound')
 require(c['countEnabled']==c['multiEnabled']==int(path=='indirect'),'feature enable')
 require(c['countSupported'] in (0,1) and c['multiSupported'] in (0,1),'support')
 if path=='indirect':require(c['countSupported']==c['multiSupported']==1 and c['maxDrawIndirectCount']>=16,'count capability')
 alloc=[x for x in rows if x['kind']=='scale_allocation']
 for z,a in enumerate(alloc):
  ints(a);require(a['ordinal']==z and a['logicalBytes']==(64 if z==0 else 272) and a['usage']==(32 if z==0 else 288) and a['requestedBytes']>=a['logicalBytes'] and a['selectedType']<32 and a['memoryTypeBits']&(1<<a['selectedType']) and a['selectedFlags']&6==6,'allocation')
 if path=='indirect':
  require(r['indirect_dependency']==dict(kind='indirect_dependency',srcStage=2048,dstStage=2,srcAccess=64,dstAccess=1,offset=0,size=272),'compute indirect dependence');ints(r['indirect_dependency'])
  require(r['argument_retirement_dependency']==dict(kind='argument_retirement_dependency',srcStage=2048,dstStage=16384,srcAccess=64,dstAccess=8192),'args host dependence');ints(r['argument_retirement_dependency'])
 words=r['commands']['values'];ints(words);require(len(words)==68,'full argument buffer')
 visible=[i for i,v in enumerate(MASK) if v]
 if path=='direct':require(words==[0]*68,'direct no fake GPU generation')
 else:
  require(words[64]==7 and words[28:64]==[0]*36 and words[65:]==[0]*3,'count and guards')
  commands=[words[n:n+4] for n in range(0,28,4)];require(commands==[[6,1,i*6,0] for i in visible],'compact exact visible set')
 actualids=visible if mode!='limited-count' else [words[n+2]//6 for n in range(0,24,4)]
 pixels=r['execution']['pixels'];ints(pixels);require(pixels==reference(actualids),'full independent pixels')
 if mode=='limited-count':require(pixels!=reference(),'truncation must actually lose visible output')
 ints(r['final']);require(r['final']==dict(kind='final',errors=0,rc=0 if mode=='good' else 6),'actual oracle exit')
 ints(r['organization']);require(r['organization']==dict(kind='organization',renderPassObjects=0,framebufferObjects=0,graphicsPipelineObjects=1,computePipelineObjects=1,renderPassBeginCalls=0,dynamicBeginCalls=1,drawCalls=7 if path=='direct' else 1,path=path),'actual calls')
 require(r['pipeline']['vertexCount']==6,'six vertices per tile')
 # Reuse common image/graphics safety gate only after actual new geometry,
 # complete pixels, count and return facts were independently checked above.
 projected=copy.deepcopy([x for x in rows if x['kind'] not in ('scale_allocation','binding_facts','scale_config','indirect_dependency','argument_retirement_dependency','commands')])
 for x in projected:
  if x['kind']=='pipeline':x['vertexCount']=3
  if x['kind']=='execution':x['pixels']=common.reference()
  if x['kind']=='organization':x['path']='dynamic';x['drawCalls']=1;x['pipelineObjects']=x.pop('graphicsPipelineObjects');x.pop('computePipelineObjects')
  if x['kind']=='final':x['rc']=0
 checked=common.check(projected,'dynamic')
 return dict(identity=checked['identity'],pixels=pixels,visibility=MASK,commands=words,draw_calls=7 if path=='direct' else 1,quality_pass=mode!='limited-count')
def decide(direct,indirect,max_recorded_draws=7,performance_required=False):
 base=dict(rule_id='C2.scale.compact-count19',limitations=['CPU batched/instanced baseline not compared.','Recorded calls are not frame performance; no physical GPU evidence.'])
 try:
  require(type(max_recorded_draws)is int and 0<=max_recorded_draws<2**32 and type(performance_required)is bool,'policy')
  a=check(direct,'direct');b=check(indirect,'indirect');require(a['identity']==b['identity'] and a['pixels']==b['pixels'],'paired quality')
 except (ValueError,KeyError,TypeError,OverflowError):return dict(base,status='UNKNOWN',selected=None)
 if performance_required:return dict(base,status='NEEDS_MEASUREMENT',selected=None)
 if max_recorded_draws<7:return dict(base,status='NEEDS_COMPARABLE_BASELINE',selected=None)
 return dict(base,status='KEEP_BASELINE',selected='direct')
