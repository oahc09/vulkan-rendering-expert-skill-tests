"""Ordinary nonindexed indirect argument layout; content/dependency separate."""
PREFIX='VUID-vkCmdDrawIndirect-'
def admit(m):
 keys=('size','usage','offset','count','stride','maxDrawIndirectCount','multiDrawEnabled','firstInstanceEnabled')
 if not isinstance(m,dict) or any(k not in m for k in keys+('multiDrawSupported','firstInstanceSupported')):return {'status':'UNKNOWN'}
 for k in keys[:-2]:
  if type(m[k]) is not int or m[k]<0:raise ValueError('nonnegative integers required')
 for k in keys[:-2]:
  if m[k]>(0xffffffffffffffff if k in ('size','offset') else 0xffffffff):raise ValueError('integer width overflow')
 for supported,enabled in (('multiDrawSupported','multiDrawEnabled'),('firstInstanceSupported','firstInstanceEnabled')):
  if type(m[supported]) is not int or m[supported] not in (0,1):return {'status':'UNKNOWN'}
  if m[enabled] and not m[supported]:return {'status':'UNKNOWN','reason':'inconsistent support and enable'}
 for k in keys[-2:]:
  if type(m[k]) is not bool:raise ValueError('enabled feature facts required')
 v=[];n=m['count']
 if n and m['offset']+16+(m['stride']*(n-1) if n>1 else 0)>0xffffffffffffffff:raise ValueError('range expression uint64 overflow')
 if not m['usage']&256:v.append(PREFIX+'buffer-02709')
 if m['offset']%4:v.append(PREFIX+'offset-02710')
 if n>1 and not m['multiDrawEnabled']:v.append(PREFIX+'drawCount-02718')
 if n>m['maxDrawIndirectCount']:v.append(PREFIX+'drawCount-02719')
 if n>1 and (m['stride']%4 or m['stride']<16):v.append(PREFIX+'drawCount-00476')
 if n==1 and m['offset']+16>m['size']:v.append(PREFIX+'drawCount-00487')
 if n>1 and m['stride']*(n-1)+m['offset']+16>m['size']:v.append(PREFIX+'drawCount-00488')
 return {'status':'REJECTED' if v else 'ARG_LAYOUT_WITHIN_SCOPE','vuids':v,'limitations':['not proof of generated command contents, execution or memory dependency']}
def content(values,*,first_instance_enabled):
 if type(first_instance_enabled) is not bool:raise ValueError('feature enabled fact')
 if not isinstance(values,list) or len(values)!=4:return {'status':'UNKNOWN'}
 if any(type(x) is not int or x<0 or x>0xffffffff for x in values):raise ValueError('VkDrawIndirectCommand uint32 words')
 if values[3] and not first_instance_enabled:return {'status':'REJECTED_FIRST_INSTANCE','vuid':'VUID-VkDrawIndirectCommand-firstInstance-00501','reason':'nonzero firstInstance requires enabled drawIndirectFirstInstance; caller must apply command-structure contract'}
 return {'status':'CONTENT_WITHIN_SCOPE','words':values,'limitations':['firstInstance feature check only; no vertex/divisor09461/09462/shader bounds proof']}
