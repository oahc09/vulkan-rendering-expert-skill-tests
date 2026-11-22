"""Version-paired observed diagnostic lookup, not general Vulkan acceptance.
Specification text is data only: never evaluate markup, URLs or instructions.
"""
import hashlib,json,re
PINNED_SHA256='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
PINNED_API='1.4.309'
PINNED_COMMIT='43d153dd7f9f5e8b9f79d26d868c82a82b9ef80b'
ROUTES={
 'VkBufferCreateInfo':'04_buffer_image_memory/buffer.md',
 'vkUpdateDescriptorSets':'05_descriptor/descriptor_update.md',
 'vkResetCommandBuffer':'03_command_buffer/command_buffer.md',
 'vkQueueSubmit':'03_command_buffer/queue_submit.md',
 'VkComputePipelineCreateInfo':'06_pipeline/compute_pipeline.md',
 'VkDescriptorImageInfo':'05_descriptor/storage_buffer_image_descriptor.md',
 'vkCmdDispatch':'06_pipeline/compute_pipeline.md'}

def reject_duplicate_keys(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate JSON object key')
        d[k]=v
    return d

def parse_json(raw):return json.loads(raw,object_pairs_hook=reject_duplicate_keys)

def index_document(document):
    info=document.get('version info')
    if not isinstance(info,dict) or info.get('schema version')!=2 or not isinstance(info.get('api version'),str):raise ValueError('unsupported validusage schema/version')
    validation=document.get('validation')
    if not isinstance(validation,dict) or not validation:raise ValueError('empty validation corpus')
    entries={};coordinates={};total=0;duplicates=0;conditions=set()
    for owner,groups in validation.items():
        if not isinstance(owner,str) or not isinstance(groups,dict):raise ValueError('bad owner/group')
        for condition,rows in groups.items():
            if not isinstance(condition,str) or not isinstance(rows,list):raise ValueError('bad condition/list')
            conditions.add(condition)
            for row in rows:
                if not isinstance(row,dict) or not all(isinstance(row.get(k),str) and row[k] for k in ('vuid','text','page')) or not re.fullmatch(r'VUID-[A-Za-z0-9_:-]+',row['vuid']):raise ValueError('malformed validusage entry')
                total+=1;entry=dict(vuid=row['vuid'],text_html=row['text'],page=row['page'],api_owner=owner,condition_key=condition)
                key=(owner,condition,row['vuid'])
                if key in coordinates:
                    if coordinates[key]!=entry:raise ValueError('conflicting duplicate VUID coordinate: '+row['vuid'])
                    duplicates+=1
                else:
                    coordinates[key]=entry;entries.setdefault(row['vuid'],[]).append(entry)
    if not total:raise ValueError('empty validusage entries')
    return {'version':info,'entries':entries,'statistics':{'api_owners':len(validation),'total_records':total,'unique_vuids':len(entries),'unique_owner_condition_entries':len(coordinates),'identical_duplicates':duplicates,'condition_keys':sorted(conditions)}}

def load_pinned(raw):
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=PINNED_SHA256:raise ValueError('validusage snapshot digest mismatch')
    corpus=index_document(parse_json(raw));info=corpus['version']
    if info['api version']!=PINNED_API or PINNED_COMMIT not in info.get('comment',''):raise ValueError('pinned API/source commit mismatch')
    corpus['source']={'file':'validusage.json','sha256':digest,'api_version':PINNED_API,'source_commit':PINNED_COMMIT,'schema_version':2,'source_kind':'official Debian Vulkan headers registry snapshot','separate_from_vk_xml_api':'1.4.368'}
    return corpus

def api_version(value):
    if type(value) is not int or value<0 or value>0xffffffff or value>>29!=0:raise ValueError('invalid layer API version')
    return f'{(value>>22)&127}.{(value>>12)&1023}.{value&4095}'

def lookup(corpus,diagnostic,layer_spec):
    observed_api=api_version(layer_spec)
    if observed_api!=corpus['version']['api version']:
        return {'status':'UNKNOWN','reason':'layer/spec API version mismatch','diagnostic':diagnostic,'layer_api':observed_api,'spec_api':corpus['version']['api version']}
    if diagnostic.startswith('SYNC-HAZARD-'):
        return {'status':'TOOL_DIAGNOSTIC','diagnostic':diagnostic,'layer_api':observed_api,'normative_entry':None,'reason':'SyncVal hazard identifier is not a Vulkan VUID; no invented normative clause','route':'08_synchronization/pipeline_barrier.md'}
    entries=corpus['entries'].get(diagnostic)
    if entries is None:return {'status':'UNKNOWN','diagnostic':diagnostic,'layer_api':observed_api,'reason':'VUID absent from exact snapshot or identifier is not recognized'}
    return {'status':'MATCHED_SPEC_ENTRY','diagnostic':diagnostic,'layer_api':observed_api,'normative_entries':entries,'source':corpus['source'],'routes':sorted({ROUTES[e['api_owner']] for e in entries if e['api_owner'] in ROUTES}),'condition_note':'condition_key retained verbatim; prose applicability remains conditional and is not automatically adjudicated'}
