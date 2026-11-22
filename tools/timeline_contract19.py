"""Ordinary timeline HOST contracts over caller-controlled snapshots, not execution."""
U64=(1<<64)-1
SOURCE={'commit':'fa30d4e312e843193601be7cb926c7e25d9ec885','path':'chapters/synchronization.adoc','sha256':'7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909'}
VU_SOURCE={'api_version':'1.4.309','sha256':'f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'}
def uint(v):return type(v) is int and 0<=v<=U64

def result(status,**kw):return {'status':status,'authority':'CALLER_FACTS_NOT_VERIFIED','whole_operation_validity':'NOT_INFERRED',**kw}

def host_signal(facts):
    keys={'ordinary_timeline_enabled','at_call_state_proven','pending_set_complete','host_calls_serialized',
          'current','value','max_difference','pending_signals','pending_waits'}
    if type(facts) is not dict or set(facts)!=keys:return result('UNKNOWN')
    for k in ('ordinary_timeline_enabled','at_call_state_proven','pending_set_complete','host_calls_serialized'):
        if type(facts[k]) is not bool or not facts[k]:return result('UNKNOWN')
    if any(not uint(facts[k]) for k in ('current','value','max_difference')):return result('UNKNOWN')
    signals,waits=facts['pending_signals'],facts['pending_waits']
    if type(signals) is not list or type(waits) is not list or any(not uint(v) for v in waits):return result('UNKNOWN')
    if any(type(s) is not dict or set(s)!={'value','happens_after_host_signal'} or not uint(s['value']) or type(s['happens_after_host_signal']) is not bool for s in signals):return result('UNKNOWN')
    v=facts['value'];ids=[]
    if v<=facts['current']:ids.append('VUID-VkSemaphoreSignalInfo-value-03258')
    if any(v>=s['value'] for s in signals):ids.append('VUID-VkSemaphoreSignalInfo-value-03259')
    if any(abs(v-x)>facts['max_difference'] for x in [facts['current'],*waits,*(s['value'] for s in signals)]):ids.append('VUID-VkSemaphoreSignalInfo-value-03260')
    ordered=all(s['happens_after_host_signal'] for s in signals)
    return result('REJECTED' if ids else ('HOST_SIGNAL_CONDITIONS_WITHIN_SCOPE' if ordered else 'ORDER_NOT_ESTABLISHED'),vuids=ids,pending_signal_order_proven=ordered,normative_source=dict(VU_SOURCE),source=dict(SOURCE),
                  limits=['Only provided ordinary timeline state; no actual API call, concurrent race or future progress simulated.','Host signal must happen before outstanding queue signals; numeric inequality does not establish ordering.'])

def wait_condition(counters,targets,mode):
    if type(mode) is not str or mode not in ('ANY','ALL') or type(counters) is not list or type(targets) is not list or not counters or len(counters)!=len(targets) or any(not uint(x) for x in counters+targets):return result('UNKNOWN')
    reached=[c>=t for c,t in zip(counters,targets)]
    return result('SNAPSHOT_PREDICATE_ONLY',satisfied=any(reached) if mode=='ANY' else all(reached),reached=reached,
                  predicts_vkresult=False,predicts_deadlock=False,all_references_retired='NOT_INFERRED',
                  limits=['Counter snapshots may immediately become stale.','Unsatisfied wait-before-signal is not proof of deadlock or of future timeout.'])

def retirement(facts):
    keys={'wait_satisfied','reference_set_complete','all_submitted_references_completed','relevant_host_calls_completed','no_concurrent_host_access'}
    if type(facts) is not dict or set(facts)!=keys or any(type(v) is not bool for v in facts.values()):return result('UNKNOWN')
    if not facts['reference_set_complete']:return result('UNKNOWN')
    return result('RETIREMENT_OBLIGATIONS_DECLARED' if all(facts[k] for k in ('all_submitted_references_completed','relevant_host_calls_completed','no_concurrent_host_access')) else 'RETIREMENT_NOT_ESTABLISHED',
                  wait_alone_sufficient=False,limits=['Complete reference retirement is caller-proven, not derived from a counter or wait.','This is not full object destruction validation (allocator, concurrent host access and ownership remain separate).'])
