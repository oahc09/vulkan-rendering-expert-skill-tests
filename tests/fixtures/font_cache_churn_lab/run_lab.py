import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import Mock
HERE=Path(__file__).resolve().parent;W,H=65,49
CASES=[('O',20,1),('O',20,1),('F',20,1),('F',20,1),('O',24,1),('O',24,1),('O',20,2)]
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def aux(folder):
 import struct
 for name,expected in [('velocity',(0.125,-0.25,0.5,1.)),('id',(37.,91.,12.,1.))]:
  b=(folder/(name+'.rgba32f')).read_bytes()
  if len(b)!=W*H*16:raise ValueError('aux size')
  values=struct.unpack('<'+str(W*H*4)+'f',b)
  if any(x!=expected[i%4] for i,x in enumerate(values)):raise ValueError('aux sentinel')
def verify(out):
 c=load(HERE.parent/'text_content_churn_lab/run_lab.py','verify_content')
 for i in range(1,7):
  for stage in ('old','retained','new'):aux(out/'frames'/str(i)/stage)
 return c.verify(out)
def pack(value,folder,quad):
 w,h=value['width'],value['height'];pixels=[x/255 for x in value['pixels']]
 if not 0<w<W-2 or not 0<h<H-2:raise ValueError('fixed atlas budget')
 atlas=[0.]*(W*H)
 for y in range(h):
  for x in range(w):atlas[(y+1)*W+x+1]=pixels[y*w+x]
 vertices=[]
 for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:vertices.extend([2*(8+x)/W-1,2*(8+y)/H-1,(1+x)/W,(1+y)/H])
 folder.mkdir(parents=True);quad.raw(folder/'atlas.f32',atlas);quad.raw(folder/'vertices.f32',vertices)
 return {'glyphs':[{'size':[w,h],'pixels':pixels,'destination':[8,8]}]}
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args();out=args.out.resolve();out.mkdir(exist_ok=False)
 def run(name,cmd):
  r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
  return log
 cost=load(HERE.parent/'font_cache_cost_lab/run_lab.py','cost_producer');quad=load(HERE.parent/'text_packed_quad_lab/run_lab.py','quad')
 font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';provider=cost.Provider(font);provider.shape=Mock(wraps=provider.shape);provider.raster=Mock(wraps=provider.raster);cache=cost.Cache(provider)
 audit=[];receipts=[]
 for i,(text,size,generation) in enumerate(CASES):
  before=(provider.shape.call_count,provider.raster.call_count);receipt,values=cache.request(text,size,generation=generation);after=(provider.shape.call_count,provider.raster.call_count)
  if len(values)!=1:raise ValueError('fixed one glyph scope')
  delta=[after[k]-before[k] for k in range(2)];expected=[[1,1],[0,0],[1,1],[0,0],[0,1],[0,0],[1,1]][i]
  if delta!=expected:raise ValueError('producer audit')
  folder=out/'inputs'/str(i);pack(values[0],folder,quad)
  # Fresh provider entry bypasses both caches, independent of returned cached payload.
  fresh=provider.shape(text,'en',generation);value=provider.raster(fresh['glyphs'][0]['id'],size)
  if receipt!=fresh:raise ValueError('shape reference mismatch')
  reference={'glyphs':[{'size':[value['width'],value['height']],'pixels':[x/255 for x in value['pixels']],'destination':[8,8]}]}
  (folder/'reference.json').write_text(json.dumps(reference))
  audit.append({'input':i,'glyph_id':receipt['glyphs'][0]['id'],'pixel_size':size,'cpu_face_generation':generation,'eventual_gpu_published_generation':2*i,'shape_calls':delta[0],'raster_calls':delta[1],'owned_bytes':cache.bytes,'glyph_entries':len(cache.glyphs)});receipts.append(receipt)
 hashes=[sha(out/'inputs'/str(i)/'atlas.f32') for i in range(7)]
 if not (hashes[0]==hashes[1]==hashes[6] and hashes[2]==hashes[3] and hashes[4]==hashes[5] and len(set(hashes))==3):raise ValueError('actual content identity')
 peak=cache.peak;cache.clear();assert cache.bytes==0 and not cache.layouts and not cache.glyphs
 (out/'provider-receipts.json').write_text(json.dumps(receipts));(out/'input-hashes.json').write_text(json.dumps(hashes))
 combined=HERE.parent/'text_combined_lifecycle_lab';run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font',font]);build=out/'prepared/prepared/build'
 source=(combined/'main.cpp').read_text();marker='int main(int argc,char**argv)'
 if source.count(marker)!=1:raise ValueError('helper hook drift')
 (build/'combined_source.hpp').write_text(source.replace(marker,'int original_combined_main(int argc,char**argv)'))
 run('compile',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include',HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'cache_churn'])
 def actual(name,inputs,frames):
  log=run(name,[build/'cache_churn',build/'shaders',inputs,frames])
  if 'CACHE_CHURN_PASS validation_enabled=1' not in log or 'CACHE_CHURN_DESTROYED' not in log:raise ValueError('validation/cleanup receipt')
 actual('actual',out/'inputs',out/'frames');rows=verify(out)
 # Still-live legal data corruption: route F payload into O20 slot, vertices unchanged.
 bad=out/'wrong-route';shutil.copytree(out/'inputs',bad/'inputs');shutil.copyfile(out/'inputs/2/atlas.f32',bad/'inputs/0/atlas.f32');actual('wrong-route',bad/'inputs',bad/'frames')
 try:verify(bad)
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise AssertionError('wrong resource route accepted')
 bad_events=out/'bad-events';shutil.copytree(out/'inputs',bad_events/'inputs');shutil.copytree(out/'frames',bad_events/'frames');p=bad_events/'frames/events.jsonl';events=[json.loads(s) for s in p.read_text().splitlines()];events[1]['submission_resources']=1;p.write_text('\n'.join(map(json.dumps,events)))
 try:verify(bad_events)
 except ValueError as e:
  if 'events mismatch' not in str(e):raise
 else:raise AssertionError('retirement accounting corruption accepted')
 summary={'status':'PASS','validation_enabled':True,'cpu_input_audit':audit,'cpu_peak_owned_coverage_bytes':peak,'cpu_final_owned_coverage_bytes':cache.bytes,'positive_draw_count':18,'positive_upload_count':13,'cycles':6,'rows':rows,'wrong_resource_route_rejected':True,'retirement_record_negative_rejected':True,'scope':'pre-generated actual CPU cache products consumed by one-device Vulkan pending lifecycle; no overlapping CPU production/GPU execution','limits':['UNUSED/preserve auxiliary attachments, not active MRT','single logical device, no dual-output integration','fixed 65x49 pages, no atlas growth','cache handles/payload distinct from GPU fixture object counts','not native heap/VRAM leak or hardware performance qualification','nearest bitmap quad not shaping quality oracle']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',combined/'main.cpp',HERE.parent/'font_cache_cost_lab/cache.py',HERE.parent/'font_cache_cost_lab/run_lab.py',HERE.parent/'text_fallback_lab/adapter.py',HERE.parent/'text_packed_quad_lab/run_lab.py',HERE.parent/'text_content_churn_lab/run_lab.py']},'prepared':json.loads((out/'prepared/local-provenance.json').read_text())},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
