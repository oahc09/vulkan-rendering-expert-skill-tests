#!/usr/bin/env python3
"""Local software Vulkan render-pass timestamps, never mobile performance proof."""
import argparse,hashlib,json,math,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
INTEGRATION=HERE.parent/'text_msdf_integration_lab/run_lab.py'
def percentile(values,p):
 if not values or any(not math.isfinite(v) or v<0 for v in values):raise ValueError('invalid samples')
 return sorted(values)[max(0,math.ceil(len(values)*p)-1)]
def replace(text,old,new):
 if text.count(old)!=1:raise ValueError('upstream instrument point changed')
 return text.replace(old,new)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--font',required=True,type=Path);p.add_argument('--msdf-source',required=True,type=Path);a=p.parse_args()
 out=a.out.resolve();out.mkdir(exist_ok=False)
 conditions=dict(warmup_cycles=5,measured_cycles=30,first_mode_rotates=True,extent=[65,49],glyph='A',scale=1,phase=0,validation_enabled=True,rgba_reference_tolerance=2e-6,every_draw_readback_verified=True,statistics='nearest-rank p50/p95/max',scope='render-pass timestamps; no startup/compile/upload/readback inside GPU interval; not pure shader timing; not mobile')
 (out/'conditions.json').write_text(json.dumps(conditions,indent=2))
 prep=out/'preparation'
 with (out/'preparation.log').open('w') as log:subprocess.run([sys.executable,str(INTEGRATION),'--out',str(prep),'--font',str(a.font),'--msdf-source',str(a.msdf_source)],check=True,timeout=360,stdout=log,stderr=subprocess.STDOUT)
 build=prep/'baseline/build';header=(build/'msdf_lab_reused.hpp').read_text()
 header='#include <chrono>\n'+header
 header=replace(header,'~TextLab(){','~TextLab(){if(costQueries)vkDestroyQueryPool(device,costQueries,nullptr);')
 header=replace(header,'  std::array<std::vector<float>,3> draw(', (HERE/'instrument.txt').read_text()+'\n  std::array<std::vector<float>,3> draw(')
 header=replace(header,'    VkRenderPassBeginInfo rp{', '    submit();begin();vkCmdResetQueryPool(cb,costQueries,0,2);vkCmdWriteTimestamp(cb,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,costQueries,0);\n    VkRenderPassBeginInfo rp{')
 header=replace(header,'vkCmdEndRenderPass(cb);','vkCmdEndRenderPass(cb);vkCmdWriteTimestamp(cb,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,costQueries,1);costSubmit();begin();')
 (out/'cost_reused.hpp').write_text(header)
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(out)]
 if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 subprocess.run(cmd+[str(HERE/'main.cpp'),'-l:libvulkan.so.1','-o',str(out/'cost_lab')],check=True,timeout=180)
 r=subprocess.run([str(out/'cost_lab'),str(build/'correct'),str(prep/'binary16-shaders'),str(prep/'linear4-shaders'),str(prep/'baseline/A/atlas.rgba32f'),str(out/'samples.jsonl'),str(prep/'baseline/A/native/color.rgba32f'),str(prep/'binary16-A-native/color.rgba32f'),str(prep/'linear4-A-native/color.rgba32f')],capture_output=True,text=True,timeout=180)
 (out/'run.log').write_text(r.stdout+r.stderr)
 if r.returncode or 'VALIDATION:' in r.stderr:raise ValueError('Vulkan execution/validation failed; retained evidence')
 entries=[json.loads(line) for line in (out/'samples.jsonl').read_text().splitlines()];status=entries[-1]['status']
 result=dict(status=status,conditions=conditions,capabilities=[x for x in entries if 'capability' in x],modes={})
 if status=='MEASURED_SOFTWARE_ONLY':
  for mode in ['baseline','binary16','linear4']:
   rows=[x for x in entries if x.get('mode')==mode]
   if len(rows)!=30 or {r['cycle'] for r in rows}!=set(range(30)):raise ValueError('sample count')
   result['modes'][mode]={key:{'p50':percentile([r[key] for r in rows],.5),'p95':percentile([r[key] for r in rows],.95),'max':max(r[key] for r in rows)} for key in ['gpu_renderpass_ns','cpu_submit_ns','cpu_wait_ns']}
  if any(x['validation']!=1 for x in result['capabilities']):raise ValueError('validation disabled')
 elif status!='NOT_MEASURED':raise ValueError('unknown result')
 else:result['reason']=entries[-1].get('reason','unspecified capability failure')
 (out/'summary.json').write_text(json.dumps(result,indent=2))
 (out/'local-provenance.json').write_text(json.dumps(dict(preparation_provenance='preparation/baseline/local-provenance.json',source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'main.cpp',HERE/'instrument.txt',HERE/'run_lab.py',out/'cost_lab']}),indent=2))
 print(json.dumps(result))
if __name__=='__main__':main()
