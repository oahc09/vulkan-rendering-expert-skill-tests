"""Compile/run authored fault, patch and negative mutant using actual Vulkan."""
import argparse,hashlib,json,pathlib,re,subprocess,uuid
p=argparse.ArgumentParser();p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
here=pathlib.Path(__file__).resolve().parent
baseline=(here/'baseline.c').read_text();fixed=baseline.replace('#define TRANSFER_FIX 0','#define TRANSFER_FIX 1')
if fixed==baseline:raise ValueError('baseline patch marker missing')
# Verify the shipped patch, not just the string replacement used for the mutant.
work=a.output/'work';work.mkdir();(work/'baseline.c').write_text(baseline)
subprocess.run(['patch','--batch','--forward',str(work/'baseline.c'),str(here/'fix.patch')],check=True,capture_output=True)
if (work/'baseline.c').read_text()!=fixed:raise ValueError('patch content mismatch')
sources={'before':baseline,'after':fixed,'mutant':fixed.replace('.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT','.dstAccessMask=0')}
report={'run_id':str(uuid.uuid4()),'provenance':'authored deliberate fault injection; not external production bug','compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'patch_sha256':hashlib.sha256((here/'fix.patch').read_bytes()).hexdigest(),'loader_sha256':hashlib.sha256(pathlib.Path(a.loader).read_bytes()).hexdigest(),'cases':{}}
identities=[]
for name,src in sources.items():
 source=work/(name+'.c');source.write_text(src);exe=work/name
 subprocess.run(['gcc','-Wall','-Wextra','-Werror','-I'+a.include,str(source),a.loader,'-o',str(exe)],check=True,capture_output=True)
 r=subprocess.run([str(exe),'bad'],capture_output=True,timeout=30)
 (a.output/(name+'.json')).write_bytes(r.stdout);(a.output/(name+'.log')).write_bytes(r.stderr)
 callbacks=json.loads(r.stdout);ids=[x['pMessageIdName'] for x in callbacks]
 match=re.search(rb'RESULT matching_words=(\d+) errors=(\d+) patched=(\d+)',r.stderr)
 lines=[x[9:] for x in r.stderr.decode().splitlines() if x.startswith('IDENTITY ')]
 if not match or len(lines)!=1:raise ValueError('incomplete runtime evidence')
 identity=json.loads(lines[0]);identities.append(identity)
 if identity['device_type']!=4:raise ValueError('CPU ICD scope required')
 words,errors,patched=map(int,match.groups())
 if patched!=(0 if name=='before' else 1) or errors!=len(ids):raise ValueError('inconsistent callback/control metadata')
 if name=='after':
  if r.returncode!=0 or ids or words!=64 or errors:raise ValueError('patch failed')
 else:
  if 'SYNC-HAZARD-READ-AFTER-WRITE' not in ids or not errors or r.returncode!=(0 if name=='before' else 6):raise ValueError('negative control not detected')
 report['cases'][name]=dict(exit=r.returncode,matching_words=words,errors=errors,message_ids=ids,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),callback_sha256=hashlib.sha256(r.stdout).hexdigest())
if any(i!=identities[0] for i in identities):raise ValueError('runtime changed')
report.update(runtime_identity=identities[0],status='PASS_SCOPED_REAL_API_REGRESSION',limitations=['deliberate fault injection, not production discovery','CPU ICD only','one queue and coherent host memory','invalid command aborted by callback; bad output is not undefined driver execution evidence','not timing/performance evidence','not cross-queue/WSI/noncoherent/SC validation'])
(a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
