"""Offline explainable delivery contracts. No GPU claims, networking or mutation.

Internal JSON fields are not Vulkan API. Missing evidence never becomes support.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math, re
from pathlib import Path

STATES = {True: 'PASS', False: 'REJECTED', None: 'UNKNOWN'}

def boolean(value):
    if value is not None and type(value) is not bool:
        raise ValueError('capability must be true/false/null')
    return value

def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite number required')
    return value

def decide(profile, rules):
    """Conjunctive prerequisites; no numeric score or vendor-based selection."""
    results=[]
    for rule in rules:
        reasons=[]; unknown=[]
        for group, keys in rule['requires'].items():
            if group not in ('supported','enabled','parameters','lifecycle'):
                raise ValueError('unknown prerequisite namespace')
            for key in keys:
                state=boolean(profile.get(group,{}).get(key))
                if state is False: reasons.append(group+'.'+key)
                elif state is None: unknown.append(group+'.'+key)
        for key, limit in rule.get('budgets',{}).items():
            measured=profile.get('costs',{}).get(key)
            if measured is None: unknown.append('costs.'+key)
            elif finite(measured)<0 or finite(measured)>finite(limit): reasons.append('budget.'+key)
        status='REJECTED' if reasons else 'UNKNOWN' if unknown else 'NEEDS_MEASUREMENT'
        # Evidence eligibility is separate from successful prerequisites.
        observation=profile.get('measurements',{}).get(rule['rule_id'])
        if status=='NEEDS_MEASUREMENT' and observation is not None:
            if observation.get('scope') != profile.get('scope') or not profile.get('scope'):
                unknown.append('measurement.scope')
            elif observation.get('comparable') is not True:
                unknown.append('measurement.comparability')
            elif not observation.get('artifact_sha256') or not re.fullmatch('[0-9a-f]{64}',observation['artifact_sha256']):
                unknown.append('measurement.provenance')
            else:
                objectives=observation.get('objectives',{})
                if not objectives or any(boolean(v) is None for v in objectives.values()):
                    unknown.append('measurement.objectives')
                elif not all(objectives.values()): status='KEEP_BASELINE'
                else: status='ELIGIBLE_WITHIN_SCOPE'
        results.append({'rule_id':rule['rule_id'],'status':status,'rejected_by':reasons,
                        'missing':unknown,'fallback':rule['fallback'],
                        'alternatives':rule['alternatives'],'revisit_conditions':rule['revisit_conditions']})
    return results

def correlate(records):
    """Only exact run/device/resource-generation joins, never time proximity."""
    index={}
    for record in records:
        obj=record.get('object')
        if not obj or obj.get('id') is None or type(obj.get('generation')) is not int:
            continue
        if not record.get('run_id') or not record.get('device_scope'):
            continue
        key=(record['run_id'],record['device_scope'],obj['id'],obj['generation'])
        index.setdefault(key,[]).append(record['evidence_id'])
    return [{'run_id':k[0],'device_scope':k[1],'object':{'id':k[2],'generation':k[3]},
             'evidence_ids':v,'meaning':'identity association, not causal proof'} for k,v in sorted(index.items())]

def correlate_engine_export(raw, profile_raw):
    """Link explicit, ordered events to reviewed source and one submission."""
    if __package__:
        from .diagnostic_handoff19 import engine_next_check
        from .evidence19 import ENGINE_STAGES, digest, engine_events
    else:
        from diagnostic_handoff19 import engine_next_check
        from evidence19 import ENGINE_STAGES, digest, engine_events

    document, artifact_hash = engine_events(raw)
    profile_hash = digest(profile_raw)
    profile = json.loads(profile_raw)
    checkout = profile.get('checkout', {})
    if (profile.get('schema') != 1 or profile.get('scope') != 'SOURCE_BINDINGS_ONLY'
            or profile.get('project') != document.get('project')
            or checkout.get('sha') != document.get('project_sha')
            or not re.fullmatch('[0-9a-f]{40}', checkout.get('sha') or '')
            or document.get('source_profile_sha256') != profile_hash):
        raise ValueError('engine export does not identify this exact project profile')

    bindings = {}
    for item in profile['bindings']:
        role = item['binding']['role']
        if role in bindings:
            raise ValueError('source profile has duplicate roles')
        bindings[role] = item

    allowed_previous = {'submit': {'record'}, 'complete': {'submit'},
                        'present_request': {'submit', 'complete'},
                        'display_feedback': {'present_request'}}
    source_roles = {'present_request': {'present_request', 'present_retire'}}
    identity_fields = ('run_id', 'device_scope', 'engine_id', 'output_id',
                       'object_type', 'object_id', 'frame_id', 'submission_id')
    states = {}
    stage_counts = {}
    for row in document['events']:
        stream = tuple(row.get(k) for k in identity_fields[:4])
        if any(not isinstance(value, str) or not value.strip() for value in stream):
            raise ValueError('event is missing unique run/device/engine/output identity')
        if stream not in states:
            states[stream] = {'last_seq': -1, 'seen': set(), 'invalid': False}
        state = states[stream]
        seq, event = row.get('seq'), row.get('event_id')
        if (type(seq) is not int or seq <= state['last_seq']
                or not isinstance(event, str) or not event.strip() or event in state['seen']):
            state['invalid'] = True
        else:
            state['last_seq'] = seq
            state['seen'].add(event)
        values = tuple(row.get(k) for k in identity_fields)
        generation, stage = row.get('generation'), row.get('stage')
        if (all(isinstance(value, str) and value.strip() for value in values)
                and type(generation) is int and generation >= 0
                and stage in ('record', 'submit', 'complete', 'present_request', 'display_feedback')):
            slot = (*values, generation, stage)
            stage_counts[slot] = stage_counts.get(slot, 0) + 1

    linked = {}
    output = []
    for ordinal, row in enumerate(document['events']):
        stream = tuple(row[k] for k in identity_fields[:4])
        stage, event = row.get('stage'), row.get('event_id')
        key = tuple(row.get(k) for k in identity_fields)
        generation = row.get('generation')
        source = row.get('source')
        source = source if isinstance(source, dict) else {}
        role = source.get('role')
        binding = bindings.get(role, {}) if isinstance(role, str) else {}
        expected_result = 'accepted' if stage in ('submit', 'present_request') else 'observed'
        reason = None
        if states[stream]['invalid']:
            reason = 'duplicate, missing, or out-of-order stream identity'
        elif (any(not isinstance(value, str) or not value.strip() for value in key)
              or type(generation) is not int or generation < 0):
            reason = 'object, generation, frame, or submission identity missing'
        elif not isinstance(stage, str) or stage not in ENGINE_STAGES:
            reason = 'event stage unknown'
        elif stage_counts.get((*key, generation, stage), 0) > 1:
            reason = 'multiple events claim the same submission stage'
        elif (not isinstance(role, str) or role not in source_roles.get(stage, {stage})
              or binding.get('state') != 'OBSERVED'
              or binding.get('disposition') not in {'INITIAL', 'REUSED'}
              or binding['binding']['path'] != source.get('path')
              or binding['binding']['symbol'] != source.get('symbol')
              or not re.fullmatch('[0-9a-f]{64}', binding.get('file_sha256') or '')
              or binding['file_sha256'] != source.get('file_sha256')
              or type(source.get('line')) is not int or source['line'] not in binding.get('lines', [])):
            reason = 'source location has no matching reviewed profile binding'
        elif row.get('result') != expected_result:
            reason = 'event outcome is not established'
        previous_id = row.get('predecessor')
        if reason is None and stage in allowed_previous:
            previous = linked.get((*stream, previous_id)) if isinstance(previous_id, str) else None
            if not previous or previous[0] != (*key, generation) or previous[1] not in allowed_previous[stage]:
                reason = 'no matching earlier predecessor for this submission and generation'
            elif stage == 'display_feedback' and row.get('observation') != 'display_feedback':
                reason = 'present request does not show actual display'
        elif reason is None and previous_id is not None:
            reason = 'root event cannot declare a predecessor'
        if reason is None:
            linked[(*stream, event)] = ((*key, generation), stage)
        output.append({'raw_index': ordinal, 'event_id': event, 'stage': stage,
                       'stream': dict(zip(identity_fields[:4], stream)),
                       'object': {'type': row.get('object_type'), 'id': row.get('object_id'),
                                  'generation': generation},
                       'frame_id': row.get('frame_id'), 'submission_id': row.get('submission_id'),
                       'state': 'ASSOCIATED' if reason is None else 'UNKNOWN',
                       'reason': reason, 'observed_result': row.get('result'),
                       'source': {name: source[name] for name in
                                  ('role', 'path', 'symbol', 'line', 'file_sha256')}
                       if reason is None else None,
                       'next_check': engine_next_check(stage, reason, row.get('result')),
                       'predecessor': previous_id if reason is None else None})
    return {'scope': 'OBSERVATION_ASSOCIATION_ONLY', 'artifact_sha256': artifact_hash,
            'source_profile_sha256': profile_hash, 'project_sha': checkout['sha'],
            'events': output, 'root_cause': 'UNVERIFIED'}

def hypothesis_status(hypothesis, known_evidence):
    required=('mechanism','support','counterevidence','experiment','stop_condition')
    if any(k not in hypothesis for k in required): raise ValueError('incomplete hypothesis')
    for key in ('support','counterevidence'):
        if not set(hypothesis[key]).issubset(known_evidence): raise ValueError('unknown evidence')
    exp=hypothesis['experiment']
    if exp.get('kind')=='wait_idle_workaround': return 'INSUFFICIENT'
    if not exp.get('discriminates') or exp.get('result') not in ('supports','refutes'):
        return 'INSUFFICIENT'
    if not exp.get('evidence_id') in known_evidence: return 'INSUFFICIENT'
    return 'SUPPORTED_NOT_PROVEN' if exp['result']=='supports' else 'REFUTED'

def validate_patch(record):
    for key in ('before_evidence','mechanism','allowed_paths','changed_paths','regressions','rollback','remaining_risks'):
        if key not in record: raise ValueError('missing patch '+key)
    if not record['before_evidence'] or not record['mechanism'] or not record['rollback']:
        raise ValueError('empty patch contract')
    if not set(record['changed_paths']).issubset(record['allowed_paths']): raise ValueError('unrelated modification')
    stages=record['regressions']
    if not stages or any(v not in ('PASS','FAIL','BLOCKED','UNVERIFIED') for v in stages.values()):
        raise ValueError('invalid regression states')
    return 'VALIDATED_WITHIN_DECLARED_SCOPE' if all(v=='PASS' for v in stages.values()) else 'NOT_VERIFIED'

def compare_ab(a,b,limits):
    keys=('scene','seed','camera','resolution','device','driver','cache','instrumentation','thermal','power_mode')
    missing=[k for k in keys if a.get(k) is None or b.get(k) is None]
    different=[k for k in keys if a.get(k)!=b.get(k)]
    if missing or different: return {'status':'NOT_COMPARABLE','missing':missing,'different':different}
    output={}; violations=[]
    for metric,max_delta in limits.items():
        av=a.get('metrics',{}).get(metric); bv=b.get('metrics',{}).get(metric)
        if av is None or bv is None: return {'status':'UNVERIFIED','missing_metric':metric}
        delta=finite(bv)-finite(av); output[metric]=delta
        if delta>finite(max_delta): violations.append(metric)
    if not limits: raise ValueError('predeclared objective limits required')
    return {'status':'KEEP_BASELINE' if violations else 'WITHIN_DECLARED_LIMITS',
            'deltas':output,'violations':violations,'note':'no significance, energy or bandwidth inference'}

def retrieve_experience(cases,scope):
    hits=[]
    for case in cases:
        if case.get('state')!='reviewed' or case.get('sanitized') is not True: continue
        required=case.get('scope',{})
        if not required or any(scope.get(k)!=v for k,v in required.items()): continue
        if not case.get('evidence') or not case.get('revisit_conditions'): continue
        hits.append({'id':case['id'],'matched':copy.deepcopy(required),
                     'evidence':list(case['evidence']),'revisit_conditions':case['revisit_conditions'],
                     'authority':'scoped experience, not specification'})
    return hits

def transition_case(case,action,evidence,reviewer=None):
    result=copy.deepcopy(case)
    if not evidence: raise ValueError('transition evidence required')
    if action=='review':
        if case.get('state')!='candidate' or case.get('sanitized') is not True or not reviewer:
            raise ValueError('review requires candidate, sanitization, independent reviewer')
        result['state']='reviewed'
    elif action in ('revoke','expire'):
        if case.get('state') not in ('candidate','reviewed'): raise ValueError('already inactive')
        result['state']='revoked' if action=='revoke' else 'expired'
    else: raise ValueError('unknown transition')
    result.setdefault('history',[]).append({'action':action,'evidence':evidence,'reviewer':reviewer})
    return result

def plan_revalidation(before, after, claims):
    """Compare scoped identities against declared claim dependencies."""
    domains = {
        'project_source', 'shader_interface', 'attachment', 'retirement',
        'shader_compile', 'driver', 'validation_layer', 'device', 'tool',
        'spec_rule', 'experience', 'documentation', 'skill_package', 'tests',
    }
    keys = before.keys() | after.keys()
    changed = {key for key in keys if before.get(key) != after.get(key)}
    unclassified = sorted(changed - domains)
    # An aggregate source identity does not say which files changed. A known
    # shader or attachment change cannot prove that it covers the whole diff.
    if 'project_source' in changed:
        unclassified.append('project_source')
    package_changes = sorted(changed & {'documentation', 'skill_package'})
    results = []
    seen = set()
    for claim in claims:
        name = claim['id']
        dependencies = claim['depends_on']
        evidence = claim['evidence_sha256']
        checks = claim['checks']
        if (not name or name in seen or not dependencies
                or len(dependencies) != len(set(dependencies))
                or not set(dependencies) <= domains - {'documentation', 'skill_package'}):
            raise ValueError('invalid or duplicate claim dependency: ' + name)
        if not isinstance(checks, list) or not checks or any(not isinstance(check, str) or not check for check in checks):
            raise ValueError('claim needs named checks: ' + name)
        if not isinstance(evidence, str) or not re.fullmatch('[0-9a-f]{64}', evidence):
            raise ValueError('claim needs a source evidence SHA-256: ' + name)
        seen.add(name)
        missing = sorted(key for key in dependencies
                         if before.get(key) is None or after.get(key) is None)
        affected = sorted(changed.intersection(dependencies))
        if 'experience' in dependencies and after.get('experience') in ('revoked', 'expired'):
            status = 'HISTORICAL_ONLY'
        elif missing:
            status = 'INSUFFICIENT_ASSOCIATION'
        elif affected:
            status = 'REVALIDATE'
        elif unclassified:
            status = 'INSUFFICIENT_ASSOCIATION'
        else:
            status = 'STILL_APPLICABLE'
        results.append({'id': name, 'status': status, 'changed_dependencies': affected,
                        'missing_identities': missing, 'manual_review_required': bool(missing or unclassified),
                        'evidence_sha256': evidence,
                        'checks': checks})
    return {'scope': 'REVALIDATION_PLAN_ONLY', 'unclassified_changes': unclassified,
            'package_changes': package_changes, 'claims': results,
            'ordered_checks': list(dict.fromkeys(check for row in results
                                  if row['status'] == 'REVALIDATE' for check in row['checks'])),
            'execution': 'NOT_RUN'}

def seal(matrix):
    required=('knowledge','expert_delivery','support_matrix','release')
    if set(matrix)!=set(required): raise ValueError('four independent seals required')
    allowed={'PASS','FAIL','BLOCKED','UNVERIFIED'}
    for name,item in matrix.items():
        if item.get('status') not in allowed or not item.get('reason'): raise ValueError('state and reason required')
        if item['status']=='PASS' and not item.get('evidence'): raise ValueError('PASS needs evidence')
    return copy.deepcopy(matrix)

def upstream_preflight(facts):
    """Route declared, local observations to one bounded compatibility probe."""
    probe = facts['probe']
    if probe == 'apple':
        fields = ('os', 'architecture', 'driver_id', 'headers_sha256',
                  'subset_in_headers', 'subset_advertised')
    elif probe == 'vvl_host_wait':
        fields = ('program_sha256', 'driver_sha256', 'old_layer_sha256',
                  'fixed_layer_sha256', 'fixed_commit_verified', 'timeline_enabled',
                  'sync_validation_enabled', 'same_family_transfer_queue_count')
    elif probe == 'mesa_anv_clear':
        fields = ('mesa_version', 'driver_id', 'platform', 'same_command_buffer',
                  'same_storage_image')
    elif probe == 'emulator_quick_boot':
        fields = ('host_os', 'emulator_version', 'guest_api', 'quick_boot_snapshot')
    else:
        raise ValueError('unknown compatibility probe')
    missing = [key for key in fields if facts.get(key) is None]
    if missing:
        return {'status': 'MISSING_INPUT', 'missing': missing, 'execution': 'NOT_RUN'}
    for key in fields:
        if key.endswith('_sha256') and (not isinstance(facts[key], str)
                                       or not re.fullmatch('[0-9a-f]{64}', facts[key])):
            raise ValueError('invalid identity: ' + key)
    if probe == 'apple':
        subset_headers = boolean(facts['subset_in_headers'])
        subset_advertised = boolean(facts['subset_advertised'])
        os_major = facts.get('macos_major')
        if subset_advertised and not subset_headers:
            status = 'REQUIRES_REVIEWED_LEGACY_BUILD'
        elif facts['driver_id'] == 'VK_DRIVER_ID_MOLTENVK':
            status = 'LEGACY_PORTABILITY_PROBE' if subset_advertised else 'REVIEW_DRIVER_REPORT'
        elif facts['driver_id'] == 'VK_DRIVER_ID_MESA_KOSMICKRISP':
            if facts['os'] != 'macOS' or facts['architecture'] != 'arm64':
                status = 'OUT_OF_SCOPE'
            elif type(os_major) is not int:
                status = 'MISSING_INPUT'
            elif os_major < 26 or subset_advertised:
                status = 'OUT_OF_SCOPE'
            else:
                status = 'KOSMICKRISP_PROBE'
        else:
            status = 'REVIEW_DRIVER_REPORT'
    elif probe == 'vvl_host_wait':
        queue_count = facts['same_family_transfer_queue_count']
        if type(queue_count) is not int or queue_count < 0:
            raise ValueError('invalid same-family transfer queue count')
        ready = all([boolean(facts[key]) for key in
                     ('fixed_commit_verified', 'timeline_enabled', 'sync_validation_enabled')])
        distinct = facts['old_layer_sha256'] != facts['fixed_layer_sha256']
        status = ('VVL_AB_PROBE' if ready and distinct and queue_count >= 2
                  else 'PREREQUISITES_UNMET')
    elif probe == 'mesa_anv_clear':
        command_buffer = boolean(facts['same_command_buffer'])
        image = boolean(facts['same_storage_image'])
        status = ('ANV_CLEAR_REPLAY_ELIGIBLE'
                  if facts['driver_id'] == 'VK_DRIVER_ID_INTEL_OPEN_SOURCE_MESA'
                  and facts['platform'] == 'Intel LNL'
                  and facts['mesa_version'] in {'26.3.0', '26.3.1'}
                  and command_buffer and image else 'OUT_OF_SCOPE')
    else:
        snapshot = boolean(facts['quick_boot_snapshot'])
        status = ('QUICK_BOOT_REPLAY_ELIGIBLE'
                  if facts['host_os'] == 'Windows' and facts['guest_api'] == '37.1'
                  and facts['emulator_version'] == '37.3.10' and snapshot else 'OUT_OF_SCOPE')
    return {'status': status, 'execution': 'NOT_RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['decide','correlate','correlate-run','revalidate','upstream-preflight','business-cost','seal']);p.add_argument('input',type=Path)
    p.add_argument('--profile', type=Path, help='exact reviewed project profile for correlate-run')
    a=p.parse_args();raw=a.input.read_bytes()
    if len(raw)>2_000_000: p.error('input budget exceeded')
    if a.operation == 'correlate-run':
        if not a.profile:
            p.error('correlate-run requires --profile')
        print(json.dumps(correlate_engine_export(raw, a.profile.read_bytes()), ensure_ascii=False, indent=2))
        return
    if a.profile:
        p.error('--profile requires correlate-run')
    data=json.loads(raw)
    if a.operation == 'revalidate':
        result = plan_revalidation(data['before'], data['after'], data['claims'])
    elif a.operation == 'upstream-preflight':
        result = upstream_preflight(data)
    elif a.operation == 'business-cost':
        if __package__:
            from .business_cost21 import report
        else:
            from business_cost21 import report
        result = report(a.input.resolve().parent, data, compare_ab)
    else:
        result=decide(data['profile'],data['rules']) if a.operation=='decide' else correlate(data) if a.operation=='correlate' else seal(data)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
