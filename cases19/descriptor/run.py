"""Actual descriptor update + VVL paired with queried-limit host rules."""
import argparse,hashlib,json,pathlib,subprocess,sys,uuid
p=argparse.ArgumentParser();p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=pathlib.Path(__file__).with_name('probe.c');exe=a.output/'probe'
command=['gcc','-Wall','-Wextra','-Werror','-I'+a.include,str(source),a.loader,'-o',str(exe)]
subprocess.run(command,check=True,capture_output=True)
root=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools'));import descriptor19 as d
report={'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'loader_sha256':hashlib.sha256(pathlib.Path(a.loader).read_bytes()).hexdigest(),'build_flags':['-Wall','-Wextra','-Werror'],'run_id':str(uuid.uuid4()),'source_sha256':hashlib.sha256(pathlib.Path(__file__).with_name('probe.c').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'cases':{},'scope':'original ordinary descriptor update experiment; no shader execution or external project acceptance'}
identities=[];limit_sets=[]
for mode in ('good','whole','zero','overrun','offset-end'):
 r=subprocess.run([str(exe),mode],capture_output=True,timeout=30)
 if r.returncode:raise ValueError('probe failed')
 (a.output/(mode+'.json')).write_bytes(r.stdout)
 lines=r.stderr.decode().splitlines()
 def metadata(prefix):
  found=[json.loads(x[len(prefix):]) for x in lines if x.startswith(prefix)]
  if len(found)!=1:raise ValueError('missing/ambiguous runtime metadata')
  return found[0]
 identity=metadata('IDENTITY ');limits=metadata('LIMITS ');identities.append(identity);limit_sets.append(limits)
 if identity['device_type']!=4:raise ValueError('CPU ICD scope')
 rule=d.check(buffer_size=256,offset=256 if mode=='offset-end' else 0,range_bytes={'good':16,'whole':d.WHOLE,'zero':0,'overrun':257,'offset-end':16}[mode],max_range=limits['maxUniformBufferRange'],alignment=limits['minUniformBufferOffsetAlignment'],bound=True,uniform_usage=True,update_safe=True)
 observed=sorted(x['pMessageIdName'] for x in json.loads(r.stdout))
 if sorted(rule['vuids'])!=observed:raise ValueError('rule/VVL diagnostic disagreement')
 if (mode in ('good','whole'))!=(rule['status']=='WITHIN_CHECKED_SCOPE'):raise ValueError('positive/negative oracle mismatch')
 report['cases'][mode]=dict(rule=rule,observed_vuids=observed,callback_sha256=hashlib.sha256(r.stdout).hexdigest())
if any(x!=identities[0] for x in identities) or any(x!=limit_sets[0] for x in limit_sets):raise ValueError('runtime changed')
report.update(runtime_identity=identities[0],queried_limits=limit_sets[0],status='PASS_BOUNDED_RULE_TOOL_PAIR')
(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
