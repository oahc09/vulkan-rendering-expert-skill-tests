"""CPU-only, deliberately narrow ENG13 fixture contracts; not a production engine.

These checks demonstrate host data/publication invariants, not full Vulkan valid
usage, real asynchronous scheduling, compiler execution or GPU correctness.
"""
import hashlib
import json
import struct

ARTIFACT_FIELDS = frozenset({
    'sourceHash', 'includeDependencyHashes', 'compilerName', 'compilerVersion',
    'compilerOptions', 'sourceLanguage', 'entryPoint', 'stage',
    'targetVulkanEnvironment', 'targetSpirvEnvironment', 'requiredExtensions',
    'requiredFeatures', 'requiredLimits', 'reflectionHash',
    'interfaceContractHash', 'bytecodeHash', 'materialSchemaVersion', 'buildRevision',
})
PIPELINE_FIELDS = frozenset({'artifact', 'specialization', 'renderTargets',
                            'staticState', 'dynamicStateDeclarations', 'samples', 'featurePath'})
INDEXED_COMMAND = struct.Struct('<IIIiI')
U64_MAX = (1 << 64)-1


def canonical_key(record, required):
    if set(record) != required:
        raise ValueError('Fixture schema requires the exact documented key set')
    data=json.dumps(record,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def read_cache_envelope(payload, envelope, environment):
    """Validate outer metadata; never parse, patch or repair opaque driver bytes."""
    if (envelope.get('environment') != environment or envelope.get('length') != len(payload)
            or envelope.get('sha256') != hashlib.sha256(payload).hexdigest()):
        return None  # Caller must select a verified cold/old path, not repair bytes.
    return payload


def publishable(result, current):
    return (result.get('state') == 'Ready' and result.get('cancelled') is False
            and all(result.get(key) == current.get(key) for key in
                    ('engineGeneration', 'deviceGeneration', 'materialGeneration', 'interfaceContractHash'))
            and all(key in result and key in current for key in
                    ('engineGeneration', 'deviceGeneration', 'materialGeneration', 'interfaceContractHash')))


def reclaimable(*, submitted, completion_observed, outstanding_consumers):
    if outstanding_consumers < 0:
        raise ValueError('Invalid consumer count')
    return outstanding_consumers == 0 and (not submitted or completion_observed)


def reservation_fits(*, resident, staging_in_flight, replacement_peak, request, budget):
    values=(resident,staging_in_flight,replacement_peak,request,budget)
    if any(type(v) is not int or v<0 or v>U64_MAX for v in values):
        raise ValueError('Invalid byte budget')
    # A policy decision only; actual driver allocation can still fail.
    return resident+staging_in_flight+replacement_peak+request <= budget


def append_slot(counter, capacity):
    if type(counter) is not int or type(capacity) is not int or not 0 <= counter <= U64_MAX or type(capacity) is not int or capacity<0 or capacity>U64_MAX:
        raise ValueError('Invalid append bounds')
    return counter if counter < capacity else None


def indexed_command_end(*, offset, count, stride, buffer_size):
    """Fixture read-range check, not a replacement for API-specific VUID checks."""
    if any(type(v) is not int or not 0<=v<=U64_MAX for v in (offset,count,stride,buffer_size)):
        raise ValueError('Invalid unsigned range')
    if offset%4 or (count>1 and (stride%4 or stride<INDEXED_COMMAND.size)):
        raise ValueError('Invalid offset/stride for this fixture')
    end=offset if count==0 else offset+(count-1)*stride+INDEXED_COMMAND.size
    if end>U64_MAX or end>buffer_size:
        raise ValueError('Out-of-bounds indirect reads')
    return end


def sampled_mips_initialized(*, view_base_mip, relative_mips, initialized_mips):
    # Supply the full actual sampling footprint, including interpolation neighbors.
    if view_base_mip<0 or any(m<0 for m in relative_mips):
        raise ValueError('Negative mip')
    return {view_base_mip+m for m in relative_mips} <= set(initialized_mips)


def interface_fixture_matches(reflected, host):
    """Narrow declared-fixture compatibility, not a SPIR-V reflection engine.

    Descriptor indexing, runtime arrays, extensions and shader entry-point
    specialization still require the real target-specific Vulkan validation.
    """
    for binding, required in reflected['bindings'].items():
        provided=host['bindings'].get(binding)
        if provided is None:
            return False
        accepted={required['type']}
        if required['type']=='uniform_buffer':
            accepted.add('uniform_buffer_dynamic')
        if (provided['type'] not in accepted or provided['count']<required['count']
                or not set(required['stages'])<=set(provided['stages'])
                or required.get('members')!=provided.get('members')):
            return False
    seen=set()
    for provided in host['push_constants']:
        stages=set(provided['stages'])
        if (not stages or stages & seen or provided['offset']<0 or provided['offset']%4
                or provided['size']<=0 or provided['size']%4
                or provided['offset']+provided['size']>host['max_push_constants_size']):
            return False
        seen |= stages
    for required in reflected['push_constants']:
        for stage in required['stages']:
            if not any(stage in supplied['stages'] and supplied['offset']<=required['offset']
                       and supplied['offset']+supplied['size']>=required['offset']+required['size']
                       for supplied in host['push_constants']):
                return False
    return True


def binary_cache_fixture_compatible(*, binary_count, capture_data, cache_nonnull):
    """vkCreateGraphicsPipelines 09616/09617 condition fixture, not an API call.

    None means no binary-info structure; zero means a present empty structure.
    CAPTURE_DATA is an independent reason to require a null pipeline cache.
    """
    if binary_count is not None and (type(binary_count) is not int or binary_count<0):
        raise ValueError('Invalid binary count')
    requires_null=capture_data or (binary_count is not None and binary_count>0)
    return not (requires_null and cache_nonnull)
