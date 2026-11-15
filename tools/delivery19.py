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

def seal(matrix):
    required=('knowledge','expert_delivery','support_matrix','release')
    if set(matrix)!=set(required): raise ValueError('four independent seals required')
    allowed={'PASS','FAIL','BLOCKED','UNVERIFIED'}
    for name,item in matrix.items():
        if item.get('status') not in allowed or not item.get('reason'): raise ValueError('state and reason required')
        if item['status']=='PASS' and not item.get('evidence'): raise ValueError('PASS needs evidence')
    return copy.deepcopy(matrix)

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['decide','correlate','seal']);p.add_argument('input',type=Path)
    a=p.parse_args();raw=a.input.read_bytes()
    if len(raw)>2_000_000: p.error('input budget exceeded')
    data=json.loads(raw)
    result=decide(data['profile'],data['rules']) if a.operation=='decide' else correlate(data) if a.operation=='correlate' else seal(data)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
