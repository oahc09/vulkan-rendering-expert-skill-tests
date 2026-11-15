#!/usr/bin/env python3
import argparse,hashlib,importlib.util,json,os,struct,subprocess,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CASES=[('O','ltr','en'),('ffi','ltr','en'),('سلام','rtl','ar')]
FRAMES=[('A-initial',0),('B-initial',0),('B-A-paused',1),('B-A-destroyed',2),('A-rebuilt',2),('B-A-rebuilt',0),('A-before-failure',1),('B-after-failure',1)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
 oracle=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap_oracle');rows=[]
 for name,index in FRAMES:
  folder=out/'frames'/name
  if (folder/'mask.f32').read_bytes()!=(out/'inputs'/(str(index)+'.f32')).read_bytes():raise ValueError('frame input association mismatch')
  row=oracle.verify(folder)
  depth=struct.unpack('<3185f',(folder/'gpu/depth.f32').read_bytes())
  if any(v!=.375 for v in depth):raise ValueError('depth protection mismatch')
  row['frame']=name;rows.append(row)
 events=[json.loads(x) for x in (out/'frames/events.jsonl').read_text().splitlines()]
 expected=[]
 for phase,live,created,destroyed,af,bf,gen in [('both_created',2,2,0,1,1,0),('A_paused_B_rendered',2,2,0,1,2,0),('A_destroyed_B_rendered',1,2,1,0,3,-1),('A_rebuilt_B_rendered',2,3,1,1,4,1),('A_failure_cleaned_B_rendered',1,3,2,0,5,-1),('legal_wrong_input_draw',1,3,2,0,6,-1)]:expected.append(dict(phase=phase,live=live,created=created,destroyed=destroyed,A_frames=af,B_frames=bf,A_generation=gen))
 expected.append(dict(phase='all_destroyed',live=0,created=3,destroyed=3))
 if events!=expected:raise ValueError('device lifecycle mismatch')
 try:oracle.verify(out/'frames/B-wrong-input')
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('wrong input image accepted')
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 if not a.font.is_file() or sha(a.font)!='57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e':raise ValueError('trusted font required')
 def run(name,args,expected=0):
  r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode!=expected or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');inputs=out/'inputs';inputs.mkdir();receipts=[]
 for i,(text,direction,language) in enumerate(CASES):
  mask,receipt=bitmap.raster(a.font,text,direction,language);receipts.append(receipt);(inputs/(str(i)+'.f32')).write_bytes(struct.pack('<3185f',*mask))
 before={p.name:sha(p) for p in inputs.iterdir()};(out/'provider-receipts.json').write_text(json.dumps(receipts,indent=2))
 base=HERE.parent/'text_vector_lab';active=HERE.parent/'text_active_mrt_lab';run('prepare-active',[sys.executable,active/'run_lab.py','--out',out/'prepared']);build=out/'prepared/build';source=(build/'active_lab_reused.hpp').read_text()
 (build/'dual_helper.hpp').write_text(source)
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'dual'];run('compile',cmd)
 log=run('vulkan',[build/'dual',build/'shaders',inputs,out/'frames'])
 if 'DUAL_DEVICE_PASS validation_enabled=1' not in log:raise ValueError('validation required')
 if before!={p.name:sha(p) for p in inputs.iterdir()}:raise ValueError('CPU input files mutated')
 # Fixed expected association, never selected by GPU logs; no reference from outputs.
 for name,index in FRAMES+[('B-wrong-input',1)]:
  folder=out/'frames'/name;(folder/'mask.f32').write_bytes((inputs/(str(index)+'.f32')).read_bytes());(folder/'gpu').mkdir()
  for f in ['color.rgba32f','velocity.rgba32f','id.rgba32f','depth.f32']:(folder/f).rename(folder/'gpu'/f)
 rows=verify(out)
 original={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()};run('existing-output',[build/'dual',build/'shaders',inputs,out/'frames'],1)
 if original!={str(p.relative_to(out/'frames')):sha(p) for p in (out/'frames').rglob('*') if p.is_file()}:raise ValueError('overwrite')
 summary=dict(status='PASS',validation_enabled=True,active_color_attachments_per_output=3,depth_protected_pixels_per_output=3185,logical_devices_created=3,peak_live_devices=2,actual_draws=9,rows=rows,negative_checks=['paused output rejected without draw','legal wrong-input GPU readback rejected','controlled completed-draw failure cleaned A; B still rendered','existing output refused unchanged'],scope='serial two logical Vulkan devices/outputs using same configured software Vulkan implementation; read-only CPU glyph masks shared',limits=['not different physical GPUs','not concurrent queues','not production memory-leak proof','failure after completed draw, not arbitrary pending/device-loss','no target hardware/Live acceptance']);(out/'summary.json').write_text(json.dumps(summary,indent=2))
 tools={}
 for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
  p=Path(shutil.which(os.environ.get(key,default)));tools[key]={'sha256':sha(p),'version':run('version-'+key,[p,'--version'])}
 runtime={}
 manifests=[Path(p) for p in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep) if p]+[p for d in os.environ.get('VK_LAYER_PATH','').split(os.pathsep) if d for p in Path(d).glob('*validation*.json')]
 for p in manifests:
  runtime[str(p)]=sha(p);j=json.loads(p.read_text());lib=j.get('ICD',j.get('layer',{}))['library_path'];candidates=[Path(lib)] if Path(lib).is_absolute() else [p.parent/lib,*[Path(d)/lib for d in os.environ.get('LD_LIBRARY_PATH','').split(os.pathsep) if d]];real=next(x for x in candidates if x.is_file());runtime[str(real)]=sha(real)
 (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'run_lab.py',HERE/'main.cpp',base/'main.cpp',base/'build.sh',active/'run_lab.py',active/'active.frag',HERE.parent/'engine_scale_lab/main.cpp',HERE.parent/'text_bitmap_lab/run_lab.py',ROOT/'tests/platform_text_probe.py']},'tools':tools,'runtime':runtime,'input_sha256':before,'binary_sha256':sha(build/'dual'),'generated_helper_sha256':sha(build/'dual_helper.hpp')},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
