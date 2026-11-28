"""Read-only thin adapters. Inputs stay local; output omits raw messages/paths.

Validation consumes application-serialized VkDebugUtilsMessengerCallbackDataEXT
fields, not an invented VVL log schema. Perfetto consumes its CSV SQL export.
Missing joins remain null. Successful parsing is not tool/device validation.
"""
import argparse,csv,hashlib,io,json,os,re
from pathlib import Path
MAX_BYTES=2_000_000
SQL='SELECT id, ts, dur, track_id, name FROM slice ORDER BY id LIMIT 10001;'
ENGINE_STAGES = {
    'cpu_span', 'record', 'submit', 'complete', 'present_request', 'display_feedback',
}
LEGACY_LOG_MAX_BYTES = 128 * 1024 * 1024
LEGACY_MARKERS = {
    "probe_marker": re.compile(rb"PROBE INSTALLED"),
    "image_barrier_marker": re.compile(
        rb"IMG_BARRIER cb=[0-9A-Fa-f]+ img=[0-9A-Fa-f]+ [A-Z0-9_]+->[A-Z0-9_]+"
        rb" srcAcc=0x[0-9A-Fa-f]+ dstAcc=0x[0-9A-Fa-f]+ mip=[0-9]+ mips=[0-9]+"
    ),
    "begin_pass_marker": re.compile(rb"BEGIN_PASS cb=[0-9A-Fa-f]+ rp=[0-9A-Fa-f]+ fb=[0-9A-Fa-f]+"),
    "draw_marker": re.compile(rb"DRAW #[0-9]+ cb=[0-9A-Fa-f]+"),
    "present_marker": re.compile(rb"PRESENT"),
}
VVL_HOST_WAIT_CASES = {
    "positive": ("PositiveSyncValTimelineSemaphore", "HostWaitPreservesCrossQueueDependency"),
    "negative": ("NegativeSyncValTimelineSemaphore", "WaitInitialValueTwoQueues"),
}

def digest(raw):
    if len(raw)>MAX_BYTES: raise ValueError('input budget exceeded')
    return hashlib.sha256(raw).hexdigest()

def validation(raw,run_id,tool_version,device_scope):
    sha=digest(raw); data=json.loads(raw)
    if not isinstance(data,list) or len(data)>10000: raise ValueError('callback array required')
    result=[]
    for i,item in enumerate(data):
        if not isinstance(item,dict): raise ValueError('callback object required')
        mid=item.get('pMessageIdName')
        if not isinstance(mid,str) or len(mid)>512: raise ValueError('missing message id')
        message=item.get('pMessage','')
        if not isinstance(message,str): raise ValueError('message must be string')
        objects=item.get('pObjects',[])
        if not isinstance(objects,list) or item.get('objectCount')!=len(objects): raise ValueError('object count mismatch')
        # Handles alone cannot be assigned an engine generation or source line.
        result.append({'evidence_id':f'validation-{sha[:12]}-{i}','kind':'validation',
            'run_id':run_id,'device_scope':device_scope,'tool':{'name':'Vulkan Validation callback','version':tool_version},
            'artifact_sha256':sha,'message_id':mid,'object':None,'source':None,
            'frame_submit_event':None,'object_count':len(objects),
            'hazard':re.search(r'SYNC-HAZARD-[A-Z_]+',mid).group(0) if re.search(r'SYNC-HAZARD-[A-Z_]+',mid) else None,
            'limitations':['no resource generation mapping','no automatic causal attribution','raw callback stays local']})
    return result

def perfetto_csv(raw,run_id,tool_version,device_scope):
    sha=digest(raw);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames!=['id','ts','dur','track_id','name']: raise ValueError('unexpected query schema')
    out=[]; seen=set()
    for row in reader:
        if len(out)>=10000: raise ValueError('row budget exceeded; query may be truncated')
        sid=int(row['id']);ts=int(row['ts']);dur=int(row['dur']);track=int(row['track_id'])
        if sid in seen or sid<0 or ts<0 or dur < -1 or track<0: raise ValueError('invalid slice')
        seen.add(sid)
        out.append({'evidence_id':f'trace-{sha[:12]}-{sid}','kind':'trace','run_id':run_id,
            'device_scope':device_scope,'tool':{'name':'Perfetto Trace Processor CSV','version':tool_version},
            'artifact_sha256':sha,'frame_submit_event':None,'object':None,'source':None,
            'slice_id':sid,'track_id':track,'ts_ns':ts,'duration_ns':dur if dur>=0 else None,
            'limitations':['trace clock only; no GPU clock calibration','slice names omitted','unfinished slice' if dur==-1 else 'not a frame/present inference']})
    return out

def engine_events(raw):
    """Read one ordered application export without inventing missing keys."""
    sha = digest(raw)
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON field: ' + key)
            result[key] = value
        return result

    data = json.loads(raw, object_pairs_hook=unique_fields)
    if (not isinstance(data, dict) or data.get('schema') != 'engine-events-v21'
            or not isinstance(data.get('events'), list) or len(data['events']) > 10000):
        raise ValueError('bounded engine-events-v21 export required')
    if not all(isinstance(row, dict) for row in data['events']):
        raise ValueError('event records must be objects')
    return data, sha

def legacy_probe_summary(path):
    """Summarize the historical Cocos diagnostic log without reusing handle IDs."""
    markers = {name: {"count": 0, "first_line": None, "last_line": None}
               for name in LEGACY_MARKERS}
    checksum = hashlib.sha256()
    size = 0
    unparsed = 0
    lines = 0
    with path.open("rb") as source:
        initial = os.fstat(source.fileno())
        if initial.st_size > LEGACY_LOG_MAX_BYTES:
            raise ValueError("legacy probe log exceeds local size budget")
        while raw := source.readline(4097):
            lines += 1
            size += len(raw)
            if len(raw) > 4096 or size > LEGACY_LOG_MAX_BYTES:
                raise ValueError("legacy probe log exceeds scan budget")
            checksum.update(raw)
            line = raw.rstrip(b"\r\n")
            for name, pattern in LEGACY_MARKERS.items():
                if pattern.fullmatch(line):
                    record = markers[name]
                    if not record["count"]:
                        record["first_line"] = lines
                    record["count"] += 1
                    record["last_line"] = lines
                    break
            else:
                unparsed += 1
        final = os.fstat(source.fileno())
        if (size != initial.st_size
                or (final.st_size, final.st_mtime_ns) != (initial.st_size, initial.st_mtime_ns)):
            raise ValueError("legacy probe log changed during scan")
    return {
        "scope": "HISTORICAL_MARKERS_ONLY",
        "artifact_sha256": checksum.hexdigest(), "bytes": size, "lines": lines,
        "markers": markers, "unparsed_lines": unparsed, "joined_events": [],
        "run_id": None, "project_sha": None, "device_scope": None,
        "missing": ["capture-time binary/source binding", "run/device/engine/output identity",
                    "object generation and frame/submission identity",
                    "submit/present return and independent display feedback"],
        "status": "INSUFFICIENT_ASSOCIATION",
    }

def vvl_host_wait_result(raw, control):
    """Read the result of one upstream gtest filter with no layer inference."""
    suite, name = VVL_HOST_WAIT_CASES[control]
    checksum = digest(raw)
    data = json.loads(raw)
    suites = data["testsuites"]
    rows = [row for group in suites for row in group["testsuite"]]
    if (len(suites) != 1 or suites[0]["name"] != suite or len(rows) != 1
            or rows[0]["name"] != name or rows[0]["classname"] != suite):
        raise ValueError("expected exactly the pinned filtered VVL test")
    test = rows[0]
    failures = test.get("failures", [])
    hazard = any(re.search(r"\bSYNC-HAZARD-WRITE-(AFTER|RACING)-WRITE\b", row["failure"])
                 for row in failures)
    if test.get("status") == "NOTRUN" or test.get("result") in {"SKIPPED", "SUPPRESSED"}:
        status = "NOT_RUN"
    elif test.get("status") != "RUN" or test.get("result") != "COMPLETED":
        status = "UNKNOWN"
    elif failures:
        status = "FAIL"
    else:
        status = "PASS"
    return {"scope": "VVL_GTEST_OBSERVATION_ONLY", "artifact_sha256": checksum,
            "control": control, "test": f"{suite}.{name}",
            "status": status, "write_hazard_in_failures": hazard,
            "layer_and_device_identity": "REQUIRES_SEPARATE_CAPTURE"}

def main():
    p=argparse.ArgumentParser();p.add_argument('adapter',choices=['validation','perfetto','engine','legacy-probe','vvl-host-wait']);p.add_argument('input',type=Path)
    for k in ('run-id','tool-version','device-scope'):p.add_argument('--'+k)
    p.add_argument('--control', choices=VVL_HOST_WAIT_CASES)
    a=p.parse_args()
    if a.adapter == 'legacy-probe':
        print(json.dumps(legacy_probe_summary(a.input), indent=2))
        return
    raw=a.input.read_bytes()
    if a.adapter == 'vvl-host-wait':
        if not a.control:
            p.error('vvl-host-wait requires --control')
        result = vvl_host_wait_result(raw, a.control)
    elif a.adapter == 'engine':
        _, sha = engine_events(raw)
        result = {'artifact_sha256': sha, 'scope': 'PARSED_ENGINE_EXPORT_ONLY'}
    else:
        if not all((a.run_id, a.tool_version, a.device_scope)):
            p.error('validation and perfetto require --run-id, --tool-version and --device-scope')
        result=(validation if a.adapter=='validation' else perfetto_csv)(raw,a.run_id,a.tool_version,a.device_scope)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
