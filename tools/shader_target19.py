"""Bounded offline-artifact and device-feature admission, never pipeline acceptance.
Only Shader and Float64 capability meanings are covered. Unknown stays unknown.
"""
import re

def admit(*,artifact_sha256,capabilities,extensions,extraction,validation,identity,support,enabled):
 if not isinstance(artifact_sha256,str) or not re.fullmatch('[0-9a-f]{64}',artifact_sha256):raise ValueError('artifact hash')
 if not isinstance(capabilities,list) or not capabilities or any(not isinstance(x,str) or not x for x in capabilities):raise ValueError('capability list')
 if len(set(capabilities))!=len(capabilities):raise ValueError('duplicate capability')
 if not isinstance(extensions,list) or any(not isinstance(x,str) or not x for x in extensions):raise ValueError('extension list')
 if not isinstance(extraction,dict) or extraction.get('artifact_sha256')!=artifact_sha256:return {'status':'UNKNOWN','reason':'missing or mismatched capability extraction artifact'}
 if type(extraction.get('exit_code')) is not int or extraction['exit_code']!=0:return {'status':'UNKNOWN','reason':'capability extraction failed'}
 if extraction.get('capabilities')!=capabilities or extraction.get('extensions')!=extensions:return {'status':'UNKNOWN','reason':'capability or extension declaration differs from extraction'}
 if not isinstance(validation,dict):raise ValueError('validation provenance')
 if validation.get('artifact_sha256')!=artifact_sha256:return {'status':'UNKNOWN','reason':'validator observed another artifact'}
 if validation.get('target_env') not in ('vulkan1.1','vulkan1.2'):return {'status':'UNKNOWN','reason':'target environment outside bounded contract'}
 if type(validation.get('exit_code')) is not int:raise ValueError('validator exit code')
 if validation['exit_code']!=0:return {'status':'REJECTED_TARGET_VALIDATION'}
 if 'Shader' not in capabilities:return {'status':'REJECTED_MISSING_SHADER_CAPABILITY','vuid':'VUID-VkShaderModuleCreateInfo-pCode-08738'}
 if extensions or set(capabilities)-{'Shader','Float64'}:return {'status':'UNKNOWN','reason':'unreviewed extension/capability requirements'}
 keys=('run','device','generation')
 if not isinstance(identity,dict) or any(not isinstance(identity.get(k),str) or not identity[k] for k in ('run','device')) or type(identity.get('generation')) is not int or identity['generation']<0:raise ValueError('device identity')
 # Device API/SPIR-V compatibility is deliberately NOT inferred from validator target.
 if 'Float64' in capabilities:
  for facts in (support,enabled):
   if not isinstance(facts,dict) or any(type(facts.get(k)) is not type(identity[k]) or facts.get(k)!=identity[k] for k in keys):return {'status':'UNKNOWN','reason':'missing or stale device query/creation evidence'}
   if facts.get('shaderFloat64') is not None and type(facts.get('shaderFloat64')) is not bool:raise ValueError('tri-state feature fact')
  if support.get('shaderFloat64') is False:return {'status':'REJECTED_UNSUPPORTED_FLOAT64'}
  if enabled.get('shaderFloat64') is False:return {'status':'REJECTED_FLOAT64_NOT_ENABLED','vuid':'VUID-VkShaderModuleCreateInfo-pCode-08740'}
  if support.get('shaderFloat64') is None or enabled.get('shaderFloat64') is None:return {'status':'UNKNOWN','reason':'Float64 support and enablement both required'}
 return {'status':'WITHIN_CHECKED_CAPABILITY_SLICE','remaining':['device API/SPIR-V version compatibility','pipeline interfaces and specialization','stage/storage/numeric limits','actual shader execution and output','remaining Vulkan validity rules']}
