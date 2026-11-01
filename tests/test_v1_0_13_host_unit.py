"""CPU fixture unit results only: no compiler, Vulkan or phone execution."""
import hashlib
import struct
import pytest
from engine_host_contracts import (ARTIFACT_FIELDS, PIPELINE_FIELDS, INDEXED_COMMAND,
    canonical_key, read_cache_envelope, publishable, reclaimable, reservation_fits,
    append_slot, indexed_command_end, sampled_mips_initialized, U64_MAX)

pytestmark=pytest.mark.host_unit


def test_artifact_manifest_and_pipeline_key_cover_distinct_layers():
    record={key:'unit-fixture' for key in ARTIFACT_FIELDS}
    first=canonical_key(record,ARTIFACT_FIELDS)
    assert first==canonical_key(dict(reversed(list(record.items()))),ARTIFACT_FIELDS)
    for key in ARTIFACT_FIELDS:
        assert canonical_key(dict(record,**{key:'changed'}),ARTIFACT_FIELDS)!=first
    with pytest.raises(ValueError):canonical_key({'bytecodeHash':'only'},ARTIFACT_FIELDS)
    pipeline={key:'unit' for key in PIPELINE_FIELDS};pipeline['artifact']=first
    original=canonical_key(pipeline,PIPELINE_FIELDS)
    for key in PIPELINE_FIELDS:
        assert canonical_key(dict(pipeline,**{key:'different'}),PIPELINE_FIELDS)!=original


@pytest.mark.parametrize('fault',['checksum','length','driver','device','version'])
def test_bad_cache_metadata_falls_back_without_editing_opaque_bytes(fault):
    payload=b'UNIT opaque driver bytes';environment=dict(driver='driver-A',device='uuid-A',version=1)
    envelope=dict(length=len(payload),sha256=hashlib.sha256(payload).hexdigest(),environment=environment.copy())
    assert read_cache_envelope(payload,envelope,environment)==payload
    if fault=='checksum':envelope['sha256']='0'*64
    elif fault=='length':envelope['length']+=1
    else:envelope['environment'][fault]='different'
    assert read_cache_envelope(payload,envelope,environment) is None
    assert payload==b'UNIT opaque driver bytes'


@pytest.mark.parametrize('changed',['engineGeneration','deviceGeneration','materialGeneration','interfaceContractHash','cancelled','state'])
def test_late_or_cancelled_pipeline_publication_is_rejected(changed):
    current=dict(engineGeneration=2,deviceGeneration=3,materialGeneration=4,interfaceContractHash='layout-A')
    result=dict(current,state='Ready',cancelled=False)
    assert publishable(result,current)
    result[changed]='obsolete' if changed!='cancelled' else True
    assert not publishable(result,current)


def test_uploaded_and_shared_resources_wait_for_all_actual_consumers():
    assert reclaimable(submitted=False,completion_observed=False,outstanding_consumers=0)
    assert not reclaimable(submitted=True,completion_observed=False,outstanding_consumers=0)
    assert not reclaimable(submitted=True,completion_observed=True,outstanding_consumers=1)
    assert reclaimable(submitted=True,completion_observed=True,outstanding_consumers=0)


def test_staging_and_old_new_overlap_are_budgeted_not_hidden():
    args=dict(resident=40,staging_in_flight=20,replacement_peak=30,request=10,budget=100)
    assert reservation_fits(**args)
    assert not reservation_fits(**dict(args,request=11))
    assert not reservation_fits(**dict(args,resident=U64_MAX))
    with pytest.raises(ValueError):reservation_fits(**dict(args,request=-1))


def test_signed_indexed_command_abi_and_ranges():
    assert INDEXED_COMMAND.size==20
    raw=INDEXED_COMMAND.pack(3,1,0,-7,0)
    assert struct.unpack_from('<i',raw,12)[0]==-7
    assert INDEXED_COMMAND.unpack(raw)==(3,1,0,-7,0)
    assert indexed_command_end(offset=0,count=1,stride=0,buffer_size=20)==20
    assert indexed_command_end(offset=4,count=2,stride=20,buffer_size=44)==44
    assert indexed_command_end(offset=0,count=0,stride=0,buffer_size=0)==0
    for args in [dict(offset=0,count=2,stride=4,buffer_size=100),
                 dict(offset=2,count=1,stride=0,buffer_size=100),
                 dict(offset=0,count=3,stride=20,buffer_size=59),
                 dict(offset=U64_MAX-3,count=2,stride=20,buffer_size=U64_MAX)]:
        with pytest.raises(ValueError):indexed_command_end(**args)


def test_append_checks_capacity_before_writing_not_at_draw_time():
    assert append_slot(0,0) is None
    assert append_slot(2,3)==2
    assert append_slot(3,3) is None
    assert append_slot(U64_MAX,3) is None


def test_view_relative_mip_footprint_and_allocation_are_different():
    assert sampled_mips_initialized(view_base_mip=2,relative_mips=[0,1],initialized_mips=[2,3])
    assert not sampled_mips_initialized(view_base_mip=2,relative_mips=[0,1,2],initialized_mips=[2,3])
    # No allocator operation is performed or claimed by changing a sampler/view range.


def test_incomplete_publication_never_defaults_to_safe():
    current=dict(engineGeneration=2,deviceGeneration=3,materialGeneration=4,interfaceContractHash='layout-A')
    assert not publishable(dict(current,state='Ready'),current)
    assert not publishable(dict(state='Ready',cancelled=False),current)


def interface_fixture():
    binding=dict(type='uniform_buffer',count=1,stages=['vertex'],members={'model':dict(offset=0,matrixStride=16)})
    reflected=dict(bindings={(0,0):binding},push_constants=[dict(offset=0,size=16,stages=['vertex','fragment'])])
    host=dict(bindings={(0,0):dict(binding,type='uniform_buffer_dynamic',count=2,stages=['vertex','fragment'])},
              push_constants=[dict(offset=0,size=32,stages=['vertex']),dict(offset=0,size=16,stages=['fragment'])],max_push_constants_size=128)
    import copy
    return copy.deepcopy(reflected),copy.deepcopy(host)


def test_dynamic_ubo_stage_superset_and_cross_stage_push_overlap_are_accepted():
    from engine_host_contracts import interface_fixture_matches
    reflected,host=interface_fixture()
    assert interface_fixture_matches(reflected,host)


@pytest.mark.parametrize('fault',['offset','stride','stage','count','type','push_range','push_stage_duplicate'])
def test_actual_interface_mismatches_are_rejected(fault):
    import copy
    from engine_host_contracts import interface_fixture_matches
    reflected,host=copy.deepcopy(interface_fixture())
    binding=host['bindings'][(0,0)]
    if fault=='offset':binding['members']['model']['offset']=4
    elif fault=='stride':binding['members']['model']['matrixStride']=8
    elif fault=='stage':binding['stages']=['fragment']
    elif fault=='count':binding['count']=0
    elif fault=='type':binding['type']='storage_image'
    elif fault=='push_range':host['push_constants'][0]['size']=4
    else:host['push_constants'][1]['stages'].append('vertex')
    assert not interface_fixture_matches(reflected,host)


@pytest.mark.parametrize('count,capture,cache,expected',[
    (None,False,True,True), (0,False,True,True),
    (1,False,True,False), (0,True,True,False), (None,True,True,False),
    (1,True,True,False), (1,False,False,True), (0,True,False,True),
])
def test_pipeline_binary_count_and_capture_are_independent_cache_conditions(count,capture,cache,expected):
    from engine_host_contracts import binary_cache_fixture_compatible
    assert binary_cache_fixture_compatible(binary_count=count,capture_data=capture,cache_nonnull=cache) is expected
