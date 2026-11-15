"""Bounded GPU data-hazard contract over caller-proven facts, not a barrier validator.

No stage/access masks, queue submissions, evidence files or device state are
inspected. False means caller established absence; unknown facts must be None.
Source metadata identifies the normative reference, not an executed source check.
"""
SOURCE = {
    'repository': 'KhronosGroup/Vulkan-Docs',
    'commit': 'fa30d4e312e843193601be7cb926c7e25d9ec885',
    'path': 'chapters/synchronization.adoc',
    'git_blob': '7b8fc732f0184ce6acc060cbea264da4150347d8',
    'sha256': '7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909',
    'anchors': ['synchronization-dependencies-memory',
                'synchronization-dependencies-access-scopes',
                'synchronization-submission-order'],
}
BOOL_FIELDS = frozenset({
    'same_device', 'overlapping_memory', 'ordinary_accesses',
    'layout_transition', 'ownership_transfer', 'memory_domain_transfer',
    'same_queue', 'submission_order', 'host_fence_completed',
    'execution_dependency_covers_both_operations',
    'first_write_available', 'available_write_visible_to_second_access',
    'availability_visibility_ordered_between_operations',
})
FIELDS = BOOL_FIELDS | {'first_access', 'second_access'}
LIMITS = [
    'Caller-proven scoped facts only; evidence and stage/access validity are not verified.',
    'No layout, ownership, domain-transfer, atomics, shader-internal or alias-lifetime reasoning.',
    'Same-queue submission order and host retirement do not alone prove a GPU memory dependency.',
    'An insufficient declaration is not a measured race or a predicted Validation diagnostic.',
    'No whole-domain L1/L2 or release acceptance is inferred.',
]


def evaluate(facts):
    """Evaluate one ordinary overlapping GPU access pair with strict exact fields.

    Access enums are READ/WRITE. A covered execution dependency already includes
    valid scope intersection/chain evidence, supplied by the caller. For RAW/WAW,
    the availability and visibility fields refer to this precise first write and
    second access, not arbitrary globally true cache properties.
    """
    def result(status, reasons, hazard=None):
        return {'status': status, 'hazard': hazard, 'reasons': reasons,
                'source': dict(SOURCE), 'limitations': list(LIMITS),
                'evidence_authority': 'CALLER_DECLARED_NOT_VERIFIED', 'vuids': []}
    if type(facts) is not dict or set(facts) != FIELDS:
        return result('UNKNOWN', ['Missing or unexpected schema fields'])
    if any(type(facts[k]) is not bool for k in BOOL_FIELDS):
        return result('UNKNOWN', ['All scope and dependency facts require explicit booleans'])
    if any(type(facts[k]) is not str or facts[k] not in {'READ', 'WRITE'}
           for k in ('first_access', 'second_access')):
        return result('UNKNOWN', ['Only known ordinary READ/WRITE access facts are accepted'])
    if (not facts['same_device'] or not facts['overlapping_memory'] or
        not facts['ordinary_accesses'] or any(facts[k] for k in
        ('layout_transition', 'ownership_transfer', 'memory_domain_transfer'))):
        return result('OUT_OF_SCOPE', ['Requires ordinary overlapping same-device accesses without additional transition obligations'])
    pair = (facts['first_access'], facts['second_access'])
    hazard = {('WRITE', 'READ'): 'RAW', ('WRITE', 'WRITE'): 'WAW',
              ('READ', 'WRITE'): 'WAR'}.get(pair)
    if hazard is None:
        return result('NO_DATA_HAZARD_IN_SCOPE', ['Read/read has no data hazard in this limited model'])
    required = ['execution_dependency_covers_both_operations']
    if hazard in {'RAW', 'WAW'}:
        required += ['first_write_available', 'available_write_visible_to_second_access',
                     'availability_visibility_ordered_between_operations']
    missing = [key for key in required if not facts[key]]
    return result('INSUFFICIENT_DEPENDENCY' if missing else 'CALLER_FACTS_SUFFICIENT',
                  missing or ['Required scoped dependencies are declared; actual proof remains external'], hazard)


UINT64_MAX = (1 << 64) - 1


def buffer_range(offset, size, buffer_size):
    """VkBufferMemoryBarrier range only; no invented atom/alignment restriction.

    WHOLE_SIZE accepts the explicit string or its actual uint64 Vulkan sentinel.
    VUIDs here are exact frozen validusage1.4.309, separate from prose368.
    """
    def u64(v):return type(v) is int and 0 <= v <= UINT64_MAX
    if not u64(offset) or not u64(buffer_size) or not (u64(size) or type(size) is str and size=='WHOLE_SIZE'):
        return {'status':'UNKNOWN','vuids':[]}
    whole = size == 'WHOLE_SIZE' or size == UINT64_MAX
    ids=[]
    if offset >= buffer_size:ids.append('VUID-VkBufferMemoryBarrier-offset-01187')
    if not whole:
        if size == 0:ids.append('VUID-VkBufferMemoryBarrier-size-01188')
        if size > buffer_size-offset:ids.append('VUID-VkBufferMemoryBarrier-size-01189')
    return {'status':'RANGE_WITHIN_SCOPE' if not ids else 'REJECTED','vuids':ids,
            'effective_size':buffer_size-offset if whole and not ids else (size if not ids else None),
            'normative_api_version':'1.4.309',
            'normative_sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7',
            'limitations':['Range only, not barrier scope, lifetime or synchronization proof. No generic alignment requirement.']}


def ownership(facts):
    """Ordinary exclusive resource, same device/instance, retaining content.

    Valid actual family indices are caller-proven. External/foreign/special
    sentinels and concurrent sharing are not handled by this limited function.
    Caller must also rule out implicit-transfer exceptions (e.g. maintenance9).
    """
    keys={'sharing_mode','same_device','same_instance','ordinary_resource',
          'preserve_contents','families_valid','baseline_no_implicit_transfer_exception',
          'source_family','destination_family'}
    unknown={'status':'UNKNOWN','synchronization_still_required':True}
    if type(facts) is not dict or set(facts)!=keys:return unknown
    for k in keys-{'sharing_mode','source_family','destination_family'}:
        if type(facts[k]) is not bool or not facts[k]:return unknown
    if facts['sharing_mode']!='EXCLUSIVE':return unknown
    # Exclude Vulkan reserved queue family sentinel range.
    if any(type(facts[k]) is not int or not 0<=facts[k]<0xfffffffc
           for k in ('source_family','destination_family')):return unknown
    required=facts['source_family']!=facts['destination_family']
    return {'status':'OWNERSHIP_TRANSFER_REQUIRED' if required else 'NO_FAMILY_TRANSFER_REQUIRED',
            'synchronization_still_required':True,'transfer_performed_not_verified':True,
            'source_anchor':'synchronization-queue-transfers','source':dict(SOURCE)}


def host_write_submission(facts):
    """Prior ordered, available host writes can use submission's memory dependency.

    This does not infer host happens-before from CPU wall-clock order. Flush
    correctness (when required) is an externally established scoped fact.
    """
    keys={'ordinary_mapped_write','write_happens_before_submission',
          'host_domain_available','host_coherent','required_flush_completed',
          'host_memory_model_ordered','device_read_in_submission_scope',
          'no_inflight_conflicting_access'}
    if type(facts) is not dict or set(facts)!=keys or any(type(v) is not bool for v in facts.values()):
        return {'status':'UNKNOWN'}
    must=keys-{'host_coherent','required_flush_completed'}
    if not all(facts[k] for k in must) or not (facts['host_coherent'] or facts['required_flush_completed']):
        return {'status':'UNKNOWN','reason':'Submission host-write shortcut preconditions not established; no barrier recipe inferred'}
    return {'status':'EXPLICIT_HOST_WRITE_BARRIER_NOT_REQUIRED_FOR_THIS_DEPENDENCY',
            'source_anchor':'synchronization-submission-host-writes','source':dict(SOURCE),
            'evidence_authority':'CALLER_DECLARED_NOT_VERIFIED',
            'limitations':['No post-submit writes, unsequenced/non-temporal stores, pending conflict, layout or ownership proof.']}
