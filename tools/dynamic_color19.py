"""Single ordinary RGBA8 color attachment policy, no pipeline/shader/draw proof."""
def admit(m):
 keys=('supported','enabled','format','usage','viewWidth','viewHeight','width','height','layout','loadOp','storeOp','offsetX','offsetY','samples','layers','viewMask','resolveMode')
 if not isinstance(m,dict) or any(k not in m for k in keys):return {'status':'UNKNOWN','reason':'missing observed configuration'}
 if any(type(m[k]) is not int or m[k]<0 for k in keys):raise ValueError('nonnegative integer configuration required')
 if (m['offsetX'],m['offsetY'],m['samples'],m['layers'],m['viewMask'],m['resolveMode'])!=(0,0,1,1,0,0):return {'status':'OUT_OF_SCOPE','reason':'only origin0 sample1 layer1 no multiview/resolve'}
 if m['supported'] not in (0,1) or m['enabled'] not in (0,1):raise ValueError('feature boolean')
 if not m['supported']:return {'status':'UNSUPPORTED'}
 if m['format']!=37:return {'status':'OUT_OF_SCOPE','reason':'only RGBA8_UNORM supported by this contract'}
 v=[]
 if not m['enabled']:v.append('VUID-vkCmdBeginRendering-dynamicRendering-06446')
 if not m['usage']&16:v.append('VUID-VkRenderingInfo-colorAttachmentCount-06087')
 if m['width']==0:v.append('VUID-VkRenderingInfo-None-08994')
 if m['height']==0:v.append('VUID-VkRenderingInfo-None-08995')
 if m['width']>m['viewWidth']:v.append('VUID-VkRenderingInfo-pNext-06079')
 if m['height']>m['viewHeight']:v.append('VUID-VkRenderingInfo-pNext-06080')
 if m['layout'] in (0,5,6,7,8):v.append('VUID-VkRenderingAttachmentInfo-imageView-06135')
 elif m['layout'] not in (1,2):return {'status':'OUT_OF_SCOPE','reason':'extended layouts not implemented'}
 if m['loadOp'] not in (0,1,2) or m['storeOp'] not in (0,1):return {'status':'OUT_OF_SCOPE','reason':'extended load/store not implemented'}
 return {'status':'REJECTED' if v else 'CONFIG_WITHIN_SCOPE','vuids':v,'limitations':['origin0 single layer/sample/color only; no resolve/depth/stencil/multiview','actual tracked image layout, format capabilities, synchronization and object lifetimes require independent evidence']}
def content(*,load,store,prior_defined,dependency_proven,full_region):
 if any(type(x) is not bool for x in (prior_defined,dependency_proven,full_region)):raise ValueError('explicit facts required')
 if type(load) is not int or type(store) is not int or load not in (0,1,2) or store not in (0,1):return {'status':'OUT_OF_SCOPE'}
 if not full_region:return {'status':'UNKNOWN_SUBREGION'}
 if not dependency_proven:return {'status':'UNKNOWN_DEPENDENCY'}
 defined=store==0 and (load==1 or (load==0 and prior_defined))
 return {'status':'DEFINED' if defined else 'UNDEFINED','reason':'no intervening draws; CLEAR defines, LOAD preserves only defined prior content, discard does not define'}
