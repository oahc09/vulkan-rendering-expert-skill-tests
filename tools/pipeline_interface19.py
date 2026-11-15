"""Bounded SPIRV-Tools text extraction for single-entry ordinary SSBO interfaces.
Not general reflection: descriptor arrays, Uniform/UniformConstant, push constants,
multiple entrypoints, extensions and optional capabilities return UNKNOWN.
"""
import hashlib,re

def reflect(*,artifact_sha256,disassembly,extraction_sha256,validation):
 if not isinstance(artifact_sha256,str) or not re.fullmatch('[0-9a-f]{64}',artifact_sha256):raise ValueError('artifact hash')
 if not isinstance(disassembly,str):raise ValueError('disassembly text')
 if hashlib.sha256(disassembly.encode()).hexdigest()!=extraction_sha256:return {'status':'UNKNOWN','reason':'disassembly digest mismatch'}
 if not isinstance(validation,dict) or validation.get('artifact_sha256')!=artifact_sha256 or validation.get('disassembly_sha256')!=extraction_sha256 or type(validation.get('exit_code')) is not int or validation['exit_code']!=0:return {'status':'UNKNOWN','reason':'unpaired tool records'}
 if validation.get('target_env') not in ('vulkan1.1','vulkan1.2'):return {'status':'UNKNOWN','reason':'unsupported tool target'}
 caps=re.findall(r'^\s*OpCapability\s+(\w+)\s*$',disassembly,re.M)
 entries=re.findall(r'^\s*OpEntryPoint\s+(\w+)\s+%\S+\s+"([^"]+)"',disassembly,re.M)
 if caps!=['Shader'] or re.search(r'^\s*OpExtension\b',disassembly,re.M) or len(entries)!=1 or entries[0][0]!='GLCompute':return {'status':'UNKNOWN','reason':'entrypoint/capability/extension outside contract'}
 dec={};ptr={};structs=set();vars=[]
 for line in disassembly.splitlines():
  tok=line.strip().split()
  if len(tok)>=3 and tok[0]=='OpDecorate':
   key=(tok[1],tok[2]);value=tuple(tok[3:])
   if key in dec:return {'status':'UNKNOWN','reason':'duplicate decoration'}
   dec[key]=value
  if len(tok)>=4 and tok[1:3]==['=','OpTypeStruct']:structs.add(tok[0])
  if len(tok)==5 and tok[1:3]==['=','OpTypePointer']:ptr[tok[0]]=(tok[3],tok[4])
  if len(tok)>=5 and tok[1:3]==['=','OpVariable']:vars.append((tok[0],tok[3],tok[4]))
 out=[]
 for var,typ,storage in vars:
  if storage in ('Uniform','UniformConstant','PushConstant'):return {'status':'UNKNOWN','reason':'resource kind outside SSBO contract'}
  if storage!='StorageBuffer':continue
  p=ptr.get(typ)
  if not p or p[0]!=storage or p[1] not in structs or (p[1],'Block') not in dec:return {'status':'UNKNOWN','reason':'not a direct Block SSBO (arrays unsupported)'}
  coords=[]
  for tag in ('DescriptorSet','Binding'):
   value=dec.get((var,tag),())
   if len(value)!=1 or not value[0].isdigit() or int(value[0])>=2**32:return {'status':'UNKNOWN','reason':'missing/invalid resource coordinate'}
   coords.append(int(value[0]))
  out.append(dict(set=coords[0],binding=coords[1],type='storage-buffer',count=1,stage='compute'))
 if not out or len({(d['set'],d['binding']) for d in out})!=len(out):return {'status':'UNKNOWN','reason':'missing or aliased resource interface'}
 return {'status':'BOUNDED_REFLECTION','artifact_sha256':artifact_sha256,'disassembly_sha256':extraction_sha256,'entrypoint':entries[0][1],'descriptors':out}

def compare(reflection,layout,*,artifact_sha256):
 if not isinstance(reflection,dict):return {'status':'UNKNOWN','reason':'missing reflection'}
 if reflection.get('status')!='BOUNDED_REFLECTION' or reflection.get('artifact_sha256')!=artifact_sha256:return {'status':'UNKNOWN','reason':'wrong or incomplete shader interface'}
 resources=reflection.get('descriptors')
 if not isinstance(resources,list) or not resources:return {'status':'UNKNOWN','reason':'empty reflection'}
 for r in resources:
  if not isinstance(r,dict) or any(type(r.get(k)) is not int or not 0<=r[k]<2**32 for k in ('set','binding')) or r.get('type')!='storage-buffer' or type(r.get('count')) is not int or r['count']!=1 or r.get('stage')!='compute':return {'status':'UNKNOWN','reason':'malformed/out-of-scope reflected resource'}
 if len({(r['set'],r['binding']) for r in resources})!=len(resources):return {'status':'UNKNOWN','reason':'aliased reflection'}
 if not isinstance(layout,list):raise ValueError('layout records')
 bindings={}
 for b in layout:
  if not isinstance(b,dict) or any(type(b.get(k)) is not int or b[k]<0 or b[k]>=2**32 for k in ('set','binding','count')):raise ValueError('unsigned layout fields')
  if not isinstance(b.get('stages'),list) or any(not isinstance(x,str) for x in b['stages']):raise ValueError('stage list')
  key=(b['set'],b['binding'])
  if key in bindings:raise ValueError('duplicate layout binding')
  if b.get('type') not in ('storage-buffer','uniform-buffer'):return {'status':'UNKNOWN','reason':'dynamic/mutable/other layout types outside bounded contract'}
  bindings[key]=b
 issues=[]
 for r in reflection['descriptors']:
  b=bindings.get((r['set'],r['binding']))
  if not b or b['count']==0 or 'compute' not in b['stages']:issues.append('VUID-VkComputePipelineCreateInfo-layout-07988')
  elif b.get('type')!='storage-buffer':issues.append('VUID-VkComputePipelineCreateInfo-layout-07990')
 return {'status':'REJECTED_INTERFACE' if issues else 'WITHIN_CHECKED_INTERFACE','vuids':sorted(set(issues)),'remaining':['pipeline limits and specialization','buffer member offsets/ranges','descriptor writes and lifetime','memory visibility and actual dispatch output']}
