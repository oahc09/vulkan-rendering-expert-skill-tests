"""Frozen implemented HOST sub-denominator, not the whole normative denominator."""
import ast,hashlib,importlib,json
from pathlib import Path
FUNCTIONS={'sync':['evaluate','buffer_range','ownership','host_write_submission'],'layout':['push_ranges','push_compatible','compatible','bind_disturbance','pipeline_access','push_update'],'image_copy':['format_admit','representation_blocks_equal','image_region'],'image_layout':['evaluate'],'timeline':['host_signal','wait_condition','retirement'],'descriptor_update':['spill','apply'],'memory_binding':['bind','granularity','free_obligations','dedicated_allocation_size']}
HELPERS={'sync':[],'layout':['uint','stages','result','_layout','_ranges'],'image_copy':['result','u32','vector','metadata'],'image_layout':['uint','cell','result'],'timeline':['uint','result'],'descriptor_update':['u32','result','layout_valid','token'],'memory_binding':['u64','identifier','result']}
INPUTS={'sync':{'prose':'chapters/synchronization.adoc'},'layout':{'chapter':'chapters/descriptorsets.adoc','common':'chapters/commonvalidity/push_constants_common.adoc'},'image_copy':{'formats':'chapters/formats.adoc','copies':'chapters/copies.adoc','common':'chapters/commonvalidity/copy_image_common.adoc'},'image_layout':{'synchronization':'chapters/synchronization.adoc'},'timeline':{'synchronization':'chapters/synchronization.adoc'},'descriptor_update':{'descriptors':'chapters/descriptorsets.adoc'},'memory_binding':{'resources':'chapters/resources.adoc','memory':'chapters/memory.adoc'}}
CARDS={'sync':'08_synchronization/buffer_memory_barrier.md#delivery19-buffer-barrier-source-boundaries','layout':'06_pipeline/pipeline_layout.md#delivery19-layout-push-contract','image_copy':'04_buffer_image_memory/copy_blit_resolve.md#delivery19-image-copy-format-region','image_layout':'08_synchronization/image_memory_barrier.md#delivery19-image-layout-ignored-discard','timeline':'08_synchronization/timeline_semaphore.md#delivery19-timeline-host-values','descriptor_update':'05_descriptor/descriptor_update.md#delivery19-descriptor-consecutive-updates','memory_binding':'04_buffer_image_memory/memory_allocation.md#delivery19-ordinary-memory-binding'}
OBLIGATIONS={'sync':['scope intersections and access/dependency evidence','ordinary ownership/host ordering assumptions'],'layout':['caller-proven identical layout definitions','supported stage/feature/path scope'],'image_copy':['supported ordinary format metadata','per-image coordinates already interpreted; no whole-copy proof'],'image_layout':['cell inventory and current states','layout usage and transition/access dependencies'],'timeline':['current snapshot and complete pending references','host ordering, no concurrency, complete retirement evidence'],'descriptor_update':['ordinary payload validity and immutable-reference identity','all command-buffer/submit consumers tracked externally'],'memory_binding':['requirements/allocation/device identity','complete usage retirement and host access evidence']}

ENTRY_OBLIGATIONS={
 'sync.evaluate':['same_device/overlapping_memory/ordinary_accesses','exclude layout_transition/ownership_transfer/memory_domain_transfer','execution_dependency_covers_both_operations','RAW/WAW first_write_available/available_write_visible_to_second_access/availability_visibility_ordered_between_operations; WAR execution only'],
 'sync.buffer_range':['offset,size,buffer_size exact uint64 or recognized WHOLE_SIZE','no nonCoherentAtomSize alignment inference'],
 'sync.ownership':['ordinary_resource and baseline_no_implicit_transfer_exception','EXCLUSIVE sharing and source_family/destination_family identity','does not establish synchronization'],
 'sync.host_write_submission':['ordinary_mapped_write/write_happens_before_submission','host_domain_available/host_memory_model_ordered','host_coherent or required_flush_completed','device_read_in_submission_scope/no_inflight_conflicting_access'],
 'layout.push_ranges':['ranges offset/size/stages and max_size','ordinary supported core stages, 4-byte range alignment and bounds','same-stage range uniqueness; not whole pipeline layout validity'],
 'layout.push_compatible':['both ordinary complete layouts with caller-proven range definitions','identical sorted push_ranges; no descriptor-set compatibility inferred'],
 'layout.compatible':['both set_definitions hashes caller-proven; set_number exists','identical prefix0..N/push_ranges/independent_sets','handle equality not required; hash does not parse Vulkan structures'],
 'layout.bind_disturbance':['previous set-to-layout inventory complete within requested range','new_layout definition and set_number valid','no prebound pipeline obligation; not actual descriptor lifetime'],
 'layout.pipeline_access':['binding_layout/pipeline_layout definitions and set_number','undisturbed boolean externally established','pipeline bind does not mutate descriptor bindings'],
 'layout.push_update':['layout_ranges/stage_mask/offset/size/max_size','per-byte update-stage covered and every overlapping range-stage included','layout creation validity does not imply update validity'],
 'image_copy.format_admit':['source/destination supported metadata and alpha_only_format false','ordinary single-plane color/block byte and block extent facts','not complete image copy admission'],
 'image_copy.representation_blocks_equal':['source_extent/destination_extent/source_block/destination_block positive vectors','ceil block-count equality only, no unique command destination extent'],
 'image_copy.image_region':['fmt metadata/offset/extent/mip_extent/side','caller already interpreted single-image coordinates','offset alignment distinct from permitted partial edge extent; no whole command proof'],
 'image_layout.evaluate':['state exact mip/layer/layout/defined inventory','barrier API/sync2/family/layout/selection facts','usage/API/subresource scope and four transition dependency proofs','ignored same-family equal-layout barrier still needs ignored_barrier_dependencies_sufficient'],
 'timeline.host_signal':['at_call_state_proven/pending_set_complete/host_calls_serialized','current/value/max_difference exact uint64','complete pending_signals/pending_waits and happens_after_host_signal ordering'],
 'timeline.wait_condition':['counters/targets matching nonempty uint64 arrays; ANY or ALL','snapshot predicate only; no VkResult/deadlock/retirement inference'],
 'timeline.retirement':['reference_set_complete/all_submitted_references_completed','relevant_host_calls_completed/no_concurrent_host_access','wait_satisfied alone cannot retire references'],
 'descriptor_update.spill':['dense binding layout with explicit zero holes','binding/array_element/count and type/stages/flags/immutable_reference_signature','only consecutive routing; no payload/lifetime proof'],
 'descriptor_update.apply':['sets/writes/copies ordinary UBO/SSBO tokens','preconditions_proven for payload/sync/layout flags; new writes live+defined','all writes before ordered copies; copied undefined is not readable','command-buffer invalidation/pending reference obligations remain outside original helper'],
 'memory_binding.bind':['ordinary_scope_proven/allocation_creation_valid/same_device','requirements_size/alignment/type_bits vs allocation_size/type_index/offset','already_bound/requires_dedicated/dedicated exact resource identity','prefers_dedicated not mandatory; no synchronization proof'],
 'memory_binding.granularity':['same allocation offsets/requirements_size and linear classification','granularity and simultaneous usage facts','page separation only; not atom alignment or full alias synchronization'],
 'memory_binding.free_obligations':['reference_inventory_complete/all_submitted_uses_retired','host_accesses_completed/no_future_bound_resource_use','bound_object_count does not by itself forbid free; not full handle validity'],
 'memory_binding.dedicated_allocation_size':['kind/allocation_size/requirements_size/ordinary_not_imported','explicit contract_version309 equality versus368 greater-or-equal','same VUID is not cross-version equivalence or complete allocation admission']}

def sha(x):return hashlib.sha256(x).hexdigest()
def digest(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def require(ok,reason):
 if not ok:raise ValueError(reason)
def parse(raw):
 def pairs(xs):
  d={}
  for k,v in xs:require(k not in d,'duplicate JSON key');d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def canonical_ast(node):
 """Version-independent serialization of parsed AST fields, not ast.dump display.
 Preserve empty lists/None and every declared semantic field; exclude only source
 location attributes. Newly introduced fields remain visible, not silently skipped.
 """
 if isinstance(node,ast.AST):
  return {'node':type(node).__name__,'fields':{name:canonical_ast(value) for name,value in ast.iter_fields(node)}}
 if isinstance(node,list):return [canonical_ast(value) for value in node]
 if node is None or type(node) in (str,int,float,bool):return node
 if type(node)is bytes:return {'bytes_hex':node.hex()}
 if type(node)is complex:return {'complex':[node.real,node.imag]}
 if node is Ellipsis:return {'ellipsis':True}
 raise ValueError('unsupported AST field type: '+type(node).__name__)
def scan(root):
 result={}
 for family,names in FUNCTIONS.items():
  path=Path(root)/f'tools/{family}_contract19.py';raw=path.read_bytes();tree=ast.parse(raw);functions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};require(set(functions)==set(names)|set(HELPERS[family]),'unregistered/missing function; classification required')
  result[family]=dict(path=str(path.relative_to(root)),source_sha256=sha(raw),entries={name:dict(ast_sha256=digest(canonical_ast(functions[name])),signature=ast.unparse(functions[name].args),docstring=ast.get_docstring(functions[name])) for name in names},excluded_helpers={name:dict(ast_sha256=digest(canonical_ast(n)),reason='Schema/arithmetic/result helper, not an independently accepted semantic entry') for name,n in functions.items() if name in HELPERS[family]})
 return result

def replay(family,docs,vu):
 """Execute only fixed trusted original functions. Capture top-level control calls.
 Caller verifies pinned implementation bytes before invoking this function.
 """
 module=importlib.import_module('checks19.run_'+family+'_contracts');rule=module.rule;original={name:getattr(rule,name) for name in FUNCTIONS[family]};calls=[];depth=[0]
 def wrap(name,fn):
  def wrapped(*args,**kw):
   top=depth[0]==0;depth[0]+=1
   try:r=fn(*args,**kw)
   finally:depth[0]-=1
   if top:calls.append(dict(function=name,input=args,result=r))
   return r
  return wrapped
 for name,fn in original.items():setattr(rule,name,wrap(name,fn))
 try:
  inputs={key:(Path(docs)/path).read_bytes() for key,path in INPUTS[family].items()}
  report=module.run(inputs,vu) if family in ('image_copy','memory_binding') else module.run(*inputs.values(),vu)
 finally:
  for name,fn in original.items():setattr(rule,name,original[name])
 require(len(calls)==report['case_count']==len(report['cases']),'complete actual controls')
 for c,row in zip(calls,report['cases']):require(digest(c['result'])==digest(row['result']),'control output mismatch')
 return report,calls

def build_manifest(root,skill,docs,vu):
 records=scan(root)
 for family,record in records.items():
  report,calls=replay(family,docs,vu);card,anchor=CARDS[family].split('#');path=Path(skill)/'references/03_api_manual'/card;raw=path.read_bytes();require(('id="'+anchor+'"').encode()in raw,'Skill anchor')
  record.update(skill=dict(path='references/03_api_manual/'+card,anchor=anchor,sha256=sha(raw)),original_entry=f'checks19/run_{family}_contracts.py',original_entry_sha256=sha((Path(root)/f'checks19/run_{family}_contracts.py').read_bytes()),report_sha256=digest(report),implementation_sha256=report['implementation_sha256'],normative_map=report['prose'],normative_309_coordinates=report.get('vuid_coordinates',report.get('range_normative_coordinates',[])),normative_309_source=report.get('vuid_source',report.get('range_normative_source')),case_count=report['case_count'])
  for name,entry in record['entries'].items():
   entry.update(preconditions=ENTRY_OBLIGATIONS[family+'.'+name],obligation_completeness='PARTIAL_EXPLICIT_PREDICATES_NOT_COMPLETE_VULKAN_VALIDITY',required_arguments=entry['signature'],unknown_obligations='Missing/malformed/out-of-scope premises do not establish validity; statuses retain each original helper meaning.',controls=[dict(name=row['name'],input_sha256=digest(c['input']),expected_status=row.get('expected_status',row.get('expected')),result_sha256=digest(c['result'])) for c,row in zip(calls,report['cases']) if c['function']==name])
   require(entry['controls'],'unexercised semantic entry')
 return dict(schema=1,status='IMPLEMENTED_HOST_CONTRACT_SUBDENOMINATOR_ONLY',semantic_entries=23,families=records,semantic_L1_L2_completion='NOT_INFERRED',versions='368 prose and 309 VUIDs retained separately; no automatic equivalence',release_status='BLOCKED')

def verify(manifest,root,skill):
 require(type(manifest)is dict and manifest.get('semantic_entries')==23 and set(manifest.get('families',{}))==set(FUNCTIONS),'exact 7/23 registry')
 actual=scan(root)
 for family,record in manifest['families'].items():
  for key in ('path','source_sha256','excluded_helpers'):require(actual[family][key]==record[key],'frozen source/helper inventory changed '+family)
  require(set(actual[family]['entries'])==set(record['entries']),'semantic entry inventory')
  for name,entry in actual[family]['entries'].items():
   for key in ('ast_sha256','signature','docstring'):require(record['entries'][name][key]==entry[key],'semantic AST changed '+family+'/'+name)
  require(record['original_entry']==f'checks19/run_{family}_contracts.py','fixed child entry path');entry=Path(root)/record['original_entry'];require(not entry.is_symlink() and sha(entry.read_bytes())==record['original_entry_sha256'],'original child entry changed')
  for name,entry in record['entries'].items():require(entry['preconditions']==ENTRY_OBLIGATIONS[family+'.'+name] and entry['obligation_completeness']=='PARTIAL_EXPLICIT_PREDICATES_NOT_COMPLETE_VULKAN_VALIDITY','entry obligations changed')
  for rel,h in record['implementation_sha256'].items():
   path=Path(root)/rel;require(not path.is_symlink() and path.resolve().is_relative_to(Path(root).resolve()) and sha(path.read_bytes())==h,'implementation source changed')
  card=Path(skill)/record['skill']['path'];require(not card.is_symlink() and card.resolve().is_relative_to(Path(skill).resolve()) and sha(card.read_bytes())==record['skill']['sha256'],'Skill source changed')
 return dict(families=7,semantic_entries=23,excluded_helpers=sum(len(x['excluded_helpers']) for x in actual.values()),status='FROZEN_IMPLEMENTED_SUBDENOMINATOR_MATCHES',completion='NOT_INFERRED')

def verify_report(snapshot,family,actual,docs,vu):
 expected,calls=replay(family,docs,vu)
 require(digest(actual)==digest(expected)==snapshot['families'][family]['report_sha256'],'original report/control content mismatch')
 require(actual['semantic_completion']=='UNKNOWN_NOT_INFERRED' and actual['release_status']=='BLOCKED','no original gate promotion')
 return {'cases':len(calls),'status':'EXACT_ORIGINAL_HOST_CONTROLS_RECHECKED'}

def verify_rebuilt(snapshot,root,skill,docs,vu):
 rebuilt=build_manifest(root,skill,docs,vu)
 require(digest(snapshot)==digest(rebuilt),'full frozen manifest/source/controls mapping differs')
 return {'status':'EXACT_23_ENTRY_MANIFEST_REBUILT','semantic_completion':'NOT_INFERRED'}
