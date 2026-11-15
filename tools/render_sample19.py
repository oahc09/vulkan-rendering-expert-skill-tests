"""Bounded GENERAL color-write to fragment-read contract, not full SyncVal."""
def reference():
 return [[255 if x<1+y%3 else 0,255 if x==0 else 0,255 if y<2 else 0,255] for y in range(4) for x in range(4)]
def source_reference():
 return [[255 if x==0 else 0,255 if y<2 else 0,255 if x<1+y%3 else 0,255] for y in range(4) for x in range(4)]
def admit(m):
 expected={'kind':'two_pass','sameSourceView':True,'sourceLayout':1,'descriptorLayout':1,'srcStage':1024,'dstStage':128,'srcAccess':256,'dstAccess':32,'sourceHostFilled':False}
 if not isinstance(m,dict) or any(type(m.get(k)) is not type(v) or m[k]!=v for k,v in expected.items()) or type(m.get('dependencyRecorded')) is not bool:return {'status':'UNKNOWN'}
 return {'status':'WITHIN_SCOPE' if m['dependencyRecorded'] else 'MISSING_DEPENDENCY'}

def graphics(p,a,l):
 import math
 if not all(isinstance(x,dict) for x in (p,a,l)):return False
 if type(p.get('maxColorAttachments')) is not int:return False
 for k in ('viewport','scissor'):
  if not isinstance(p.get(k),list) or len(p[k])!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in p[k]):return False
 for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight','viewportBoundsMin','viewportBoundsMax'):
  if type(l.get(k)) not in (int,float) or not math.isfinite(l[k]):return False
 if type(a.get('usage')) is not int or type(a.get('format')) is not int:return False
 fixed={'format':37,'attachmentFormat':37,'colorCount':1,'samples':1,'viewMask':0,'vertexCount':3,'instanceCount':1,'stageCount':2,'stageMask':17,'topology':3,'depthStencilPresent':0,'firstVertex':0,'firstInstance':0,'blendEnable':0,'writeMask':15,'cullMode':0,'rasterizerDiscard':0}
 if any(type(p.get(k)) is not int or p[k]!=v for k,v in fixed.items()):return False
 if p.get('viewport')!=[0,0,4,4] or p.get('scissor')!=[0,0,4,4] or p.get('unusedAttachmentsEnabled') is not False:return False
 if a.get('usage')!=21 or a.get('format')!=37:return False
 return p.get('maxColorAttachments',0)>=1 and all(l.get(k,0)>=4 for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight')) and l.get('viewportBoundsMin',1)<=0 and l.get('viewportBoundsMax',0)>=4
