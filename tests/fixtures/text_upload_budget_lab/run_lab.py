#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];PAYLOAD=65*49*4

def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 events=[json.loads(x) for x in (out/'frames/events.jsonl').read_text().splitlines()];rejections=[e for e in events if e['kind']=='rejection'];steady=[e for e in events if e['kind']=='steady'];pending=[e for e in events if e['kind']=='cancel_pending']
 reasons=['dimension_nonfinite','dimension_invalid','payload_overflow','extent_unsupported','mask_size','mask_nonfinite_or_range']+['epoch_byte_limit','upload_not_complete','inflight_upload_limit','epoch_byte_limit']*3
 if [e['reason'] for e in rejections]!=reasons:raise ValueError('rejection reasons')
 if any(e['before']!=e['after'] for e in rejections):raise ValueError('rejection side effects')
 if len(steady)!=3 or len(pending)!=3:raise ValueError('cycle counts')
 for i,row in enumerate(steady):
  expected={'resident_staging_payload':0,'staging_handles':0,'epoch':2*i+2,'epoch_bytes':PAYLOAD,'inflight_bytes':0,'inflight_uploads':0,'accepted_uploads':2*i+3,'page_objects':1,'live_pages':1,'submission_objects':0,'published':2*i+2}
  if row!={'kind':'steady','cycle':i,'state':expected}:raise ValueError('steady resource mismatch')
  expected={'resident_staging_payload':PAYLOAD,'staging_handles':1,'epoch':2*i+2,'epoch_bytes':0,'inflight_bytes':PAYLOAD,'inflight_uploads':1,'accepted_uploads':2*i+2,'page_objects':2,'live_pages':2,'submission_objects':2,'published':2*i}
  if pending[i]!={'kind':'cancel_pending','cycle':i,'state':expected}:raise ValueError('cancel pending accounting')
 # Epoch-only rejection after completion is intentionally still charged although
 # actual staging/command/fence objects have already been released.
 for i,e in enumerate(rejections[6:]):
  if i%4==3 and (e['before']['epoch_bytes']!=PAYLOAD or e['before']['inflight_bytes']!=0 or e['before']['resident_staging_payload']!=0):raise ValueError('epoch refund confusion')
 q=load(HERE.parent/'text_packed_quad_lab/run_lab.py','budget_quad');rows=[]
 for cycle in range(3):
  for side,factor in [('old',1 if cycle%2==0 else .5),('new',.5 if cycle%2==0 else 1)]:
   path=out/('reference-full' if factor==1 else 'reference-half');r=q.verify(path,out/'frames'/(side+'-'+str(cycle)));r.update(cycle=cycle,stage=side);rows.append(r)
 return rows,events

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 (out/'conditions.json').write_text(json.dumps({'extent':[65,49],'payload_bytes':PAYLOAD,'epoch_upload_payload_limit':PAYLOAD,'max_inflight_upload_tasks':1,'cycles':3,'tolerance':1e-6,'scope':'fixture admission capacities, not VRAM or product performance gates'},indent=2))
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 combined=HERE.parent/'text_combined_lifecycle_lab';run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']);build=out/'prepared/prepared/build'
 s=(combined/'main.cpp').read_text();marker='int main(int argc,char**argv)'
 if s.count(marker)!=1:raise ValueError('helper hook drift')
 (build/'budget_helper.hpp').write_text(s[:s.index(marker)])
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'upload_budget'])
 (out/'reference-full').mkdir();shutil.copyfile(out/'prepared/reference.json',out/'reference-full/reference.json');shutil.copytree(out/'prepared/new-reference',out/'reference-half')
 log=run('actual',[build/'upload_budget',build/'shaders',out/'prepared/prepared/atlas.f32',out/'prepared/prepared/vertices.f32',out/'frames'])
 if 'UPLOAD_BUDGET_PASS validation_enabled=1' not in log or 'COMBINED_PENDING_CLEANUP_OK' not in log:raise ValueError('completion receipt')
 rows,events=verify(out)
 summary={'status':'PASS','validation_enabled':True,'cycles':3,'accepted_uploads':7,'rejected_requests_or_early_completion':18,'positive_images':6,'payload_capacity_bytes':PAYLOAD,'epoch_and_inflight_independent':True,'actual_owned_staging_payload_at_steady':0,'actual_owned_submission_objects_at_steady':0,'rows':rows,'accounting_events':events,'limits':['payload bytes not Vulkan allocation size or VRAM','counts exclude inherited startup resources and CPU font-service caches','no allocation/device-loss fault injection','single software Vulkan queue and fixed glyph input','no product throughput/capacity promise or target-device/Live acceptance']};(out/'summary.json').write_text(json.dumps(summary,indent=2))
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',combined/'main.cpp',combined/'run_lab.py']},'generated':{str(p):sha(p) for p in [build/'budget_helper.hpp',build/'upload_budget']},'prepared_receipt':json.loads((out/'prepared/local-provenance.json').read_text())},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
