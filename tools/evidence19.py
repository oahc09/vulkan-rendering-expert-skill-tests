"""Read-only thin adapters. Inputs stay local; output omits raw messages/paths.

Validation consumes application-serialized VkDebugUtilsMessengerCallbackDataEXT
fields, not an invented VVL log schema. Perfetto consumes its CSV SQL export.
Missing joins remain null. Successful parsing is not tool/device validation.
"""
import argparse,csv,hashlib,io,json,re
from pathlib import Path
MAX_BYTES=2_000_000
SQL='SELECT id, ts, dur, track_id, name FROM slice ORDER BY id LIMIT 10001;'

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

def main():
    p=argparse.ArgumentParser();p.add_argument('adapter',choices=['validation','perfetto']);p.add_argument('input',type=Path)
    for k in ('run-id','tool-version','device-scope'):p.add_argument('--'+k,required=True)
    a=p.parse_args();raw=a.input.read_bytes()
    result=(validation if a.adapter=='validation' else perfetto_csv)(raw,a.run_id,a.tool_version,a.device_scope)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
