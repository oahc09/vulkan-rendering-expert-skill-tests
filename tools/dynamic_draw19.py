"""Bounded fullscreen vertex+fragment sample; not full graphics-pipeline validation."""
import math
VUID='VUID-vkCmdDraw-dynamicRenderingUnusedAttachments-08910'
def admit(p,attachment,limits):
 required=('format','attachmentFormat','colorCount','samples','viewMask','unusedAttachmentsEnabled','vertexCount','instanceCount','viewport','scissor','maxColorAttachments','blendEnable','writeMask','cullMode','rasterizerDiscard','stageCount','stageMask','topology','depthStencilPresent','firstVertex','firstInstance')
 if not isinstance(p,dict) or any(k not in p for k in required):return {'status':'UNKNOWN'}
 if not isinstance(attachment,dict) or any(k not in attachment for k in ('format','samples','viewMask','enabled','layers','resolveMode','usage','width','height','viewWidth','viewHeight','layout','offsetX','offsetY','loadOp','storeOp')):return {'status':'UNKNOWN'}
 if not isinstance(limits,dict) or any(k not in limits for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight','viewportBoundsMin','viewportBoundsMax')):return {'status':'UNKNOWN'}
 for k in ('format','samples','viewMask','enabled','layers','resolveMode','usage','width','height','viewWidth','viewHeight','layout','offsetX','offsetY','loadOp','storeOp'):
  if type(attachment[k]) is not int or attachment[k]<0:raise ValueError('integer attachment facts required')
 for k,v in limits.items():
  if k!='kind' and (type(v) not in (int,float) or not math.isfinite(v)):raise ValueError('finite limits required')
 for key in ('viewport','scissor'):
  if not isinstance(p[key],list) or len(p[key])!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in p[key]):raise ValueError('finite viewport/scissor required')
 bounded={'layers':1,'resolveMode':0,'usage':17,'width':4,'height':4,'viewWidth':4,'viewHeight':4,'layout':2,'offsetX':0,'offsetY':0,'loadOp':1,'storeOp':0}
 if any(attachment[k]!=v for k,v in bounded.items()):return {'status':'OUT_OF_SCOPE','reason':'attachment outside fixed ordinary 4x4 color slice'}
 if p['format'] not in (37,44) or p['attachmentFormat']!=37:return {'status':'OUT_OF_SCOPE','reason':'only RGBA8 view with RGBA8 pipeline or explicit BGRA8 mismatch control'}
 if (p['stageMask'],p['topology'],p['depthStencilPresent'],p['firstVertex'],p['firstInstance'])!=(17,3,0,0,0):return {'status':'OUT_OF_SCOPE'}
 if p['stageCount']!=2:return {'status':'OUT_OF_SCOPE'}
 if p['unusedAttachmentsEnabled'] is not False:return {'status':'OUT_OF_SCOPE'}
 for k in ('format','attachmentFormat','colorCount','samples','viewMask','vertexCount','instanceCount','maxColorAttachments','blendEnable','writeMask','cullMode','rasterizerDiscard','stageCount','stageMask','topology','depthStencilPresent','firstVertex','firstInstance'):
  if type(p[k]) is not int or p[k]<0:raise ValueError('integer pipeline facts required')
 if (p['colorCount'],p['samples'],p['viewMask'],p['vertexCount'],p['instanceCount'],p['blendEnable'],p['writeMask'],p['cullMode'],p['rasterizerDiscard'])!=(1,1,0,3,1,0,15,0,0) or p['viewport']!=[0,0,4,4] or p['scissor']!=[0,0,4,4]:return {'status':'OUT_OF_SCOPE'}
 if attachment['enabled']!=1 or attachment['samples']!=1 or attachment['viewMask']!=0 or attachment['format']!=p['attachmentFormat']:return {'status':'UNKNOWN','reason':'inconsistent actual rendering manifest'}
 if p['maxColorAttachments']<1 or any(limits[k]<4 for k in ('framebufferWidth','framebufferHeight','viewportWidth','viewportHeight')) or limits['viewportBoundsMin']>0 or limits['viewportBoundsMax']<4:return {'status':'UNSUPPORTED_LIMITS'}
 v=[] if p['format']==p['attachmentFormat'] else [VUID]
 return {'status':'REJECTED' if v else 'DRAW_CONFIG_WITHIN_SCOPE','vuids':v,'limitations':['single color no blend/cull/depth/resolve; not general shader interface validator','object lifetime, image layout and synchronization require separate evidence']}
def reference():
 return [[255,0,0,255] if (x+y)%2==0 else [0,0,255,255] for y in range(4) for x in range(4)]
