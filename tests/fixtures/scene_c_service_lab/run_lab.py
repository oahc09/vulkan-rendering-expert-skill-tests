import argparse,copy,shutil,hashlib,importlib.util,json,os,select,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FIX=HERE.parent;W,H=65,49
OLD=[(1,1),(17,1),(33,1),(49,1),(1,18),(17,18),(33,18),(49,18)];NEW=(32,34)
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Service:
 def __init__(self,binary,shader,root):
  self.root=root;root.mkdir();(root/'requests').mkdir();self.log=open(root/'stdout.log','wb');self.err=open(root/'stderr.log','wb');self.p=subprocess.Popen([str(binary),str(shader),str(root/'requests'),str(root/'frames')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err);self.buf=b'';self.seq=0;self.events=[];self.closed=False
  try:self.wait('READY')
  except BaseException:self.close(False);raise
 def wait(self,op):
  deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   if b'\n' in self.buf:
    line,self.buf=self.buf.split(b'\n',1)
    if line.startswith(b'ACK '):
     r=json.loads(line[4:]);assert r['seq']==self.seq and r['op']==op;self.events.append(r);return r
    continue
   ready,_,_=select.select([self.p.stdout],[],[],max(0,deadline-time.monotonic()))
   if not ready:break
   b=os.read(self.p.stdout.fileno(),4096)
   if not b:raise RuntimeError('service EOF before '+op)
   self.log.write(b);self.log.flush();self.buf+=b
  raise TimeoutError('bounded ACK '+op)
 def request_dir(self):
  d=self.root/'requests'/str(self.seq+1);d.mkdir();return d
 def send(self,op):
  self.seq+=1;self.p.stdin.write(f'{op} {self.seq}\n'.encode());self.p.stdin.flush();return self.wait(op)
 def close(self,success=False):
  if self.closed:return
  timed_out=False
  try:
   if self.p.stdin and not self.p.stdin.closed:self.p.stdin.close()
   try:self.p.wait(timeout=45)
   except subprocess.TimeoutExpired:self.p.kill();self.p.wait();timed_out=True
  finally:
   tail=self.p.stdout.read();self.log.write(tail);self.log.close();self.err.close();self.closed=True
  log=(self.root/'stdout.log').read_text()+(self.root/'stderr.log').read_text()
  if timed_out:raise RuntimeError('service cleanup timeout')
  if 'VALIDATION:' in log:raise RuntimeError('validation failure')
  if success and (self.p.returncode!=0 or 'SERVICE_DESTROYED validation_enabled=1' not in log):raise RuntimeError('service cleanup receipt')
def vertices(placements,destinations):
 result=[]
 for p,(dx,dy) in zip(placements,destinations):
  assert 0<=dx and 0<=dy and dx+p.width<=W and dy+p.height<=H
  for x,y in [(0,0),(p.width,0),(0,p.height),(0,p.height),(p.width,0),(p.width,p.height)]:result.extend([2*(dx+x)/W-1,2*(dy+y)/H-1,(p.x+x)/W,(p.y+y)/H])
 return result

def exercise(binary,shader,root,quad):
 cost=load(FIX/'font_cache_cost_lab/run_lab.py','service_cost');packing=load(HERE.parents[1]/'text_atlas_packing.py','service_packing');font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 service=Service(binary,shader,root);cache=None;trace=[]
 try:
  provider=cost.Provider(font);fresh=cost.Provider(font);cache=cost.Cache(provider);atlas=packing.ShelfAtlas(W,H,max_pages=2,padding=1)
  def produce(text):
   before=provider.calls.copy();begin=time.monotonic_ns();r,gs=cache.request(text,20);end=time.monotonic_ns();ref=fresh.shape(text,'en',1);g=fresh.raster(ref['glyphs'][0]['id'],20)
   assert r==ref and len(gs)==1 and gs[0]==g
   trace.append({'after_ack_seq':service.seq,'text':text,'begin_ns':begin,'end_ns':end,'hb_delta':provider.calls['hb']-before['hb'],'ft_delta':provider.calls['ft']-before['ft'],'owned_bytes':cache.bytes})
   return gs[0],g
  o,ro=produce('O');assert (o['width'],o['height'])==(14,15)
  for _ in range(7):hot,_=produce('O');assert hot==o and trace[-1]['hb_delta']==trace[-1]['ft_delta']==0
  rect=lambda g:(g['width'],g['height'],[x/255 for x in g['pixels']])
  batch=atlas.prepare([rect(o)]*8);placements=batch.placements
  assert [(p.page,p.x,p.y,p.width,p.height) for p in placements]==[(0,x,y,14,15) for x,y in OLD]
  atlas.publish(batch);old_snapshot=atlas.snapshot();old_uv=vertices(placements,OLD)
  d=service.request_dir();quad.raw(d/'page0.f32',old_snapshot[0]);quad.raw(d/'old.f32',old_uv);r=service.send('INIT');assert (r['A_submissions'],r['B_submissions'],r['B_live_pages'])==(1,0,1)
  # First F production only AFTER actual A pending ACK.
  f,rf=produce('F');assert trace[-1]['after_ack_seq']==1 and trace[-1]['hb_delta']==trace[-1]['ft_delta']==1 and (f['width'],f['height'])==(10,15)
  batch=atlas.prepare([rect(f)]);assert len(batch.pages)==2 and [(p.page,p.x,p.y) for p in batch.placements]==[(1,1,1)]
  new_uv=vertices(batch.placements,[NEW]);d=service.request_dir();quad.raw(d/'page1.f32',batch.pages[1]['pixels']);quad.raw(d/'new.f32',new_uv)
  r=service.send('PREPARE');assert (r['A_submissions'],r['B_submissions'],r['B_live_pages'])==(1,2,2)
  pending=r.copy();r=service.send('CANCEL');assert all(r[k]==pending[k] for k in ('A_submissions','B_submissions','B_live_pages','B_epoch'));packing.ShelfAtlas.cancel(batch)
  r=service.send('RELEASE_B');assert r['B_submissions']==0 and r['B_live_pages']==1 and atlas.snapshot()==old_snapshot
  f2,_=produce('F');assert f2==f and trace[-1]['after_ack_seq']==4 and trace[-1]['hb_delta']==trace[-1]['ft_delta']==0
  grown=atlas.prepare([rect(f2)]);assert tuple(grown.pages[0]['pixels'])==old_snapshot[0] and vertices(grown.placements,[NEW])==new_uv
  d=service.request_dir();quad.raw(d/'page1.f32',grown.pages[1]['pixels']);quad.raw(d/'new.f32',new_uv);r=service.send('GROW');assert r['B_epoch']==2 and r['B_live_pages']==2 and r['B_submissions']==0
  atlas.publish(grown);assert atlas.snapshot()[0]==old_snapshot[0] and vertices(placements,OLD)==old_uv
  before=service.send('STATE');saved=atlas.snapshot();revision=atlas.revision
  try:atlas.prepare([rect(o)]*16)
  except ValueError as e:assert str(e)=='page budget exceeded'
  else:raise AssertionError('overflow accepted')
  assert atlas.snapshot()==saved and atlas.revision==revision
  after=service.send('STATE');assert {k:v for k,v in before.items() if k!='seq'}=={k:v for k,v in after.items() if k!='seq'}
  service.send('WRONG');service.send('RELEASE_A')
  d=service.request_dir();quad.raw(d/'page0.f32',saved[0]);quad.raw(d/'page1.f32',saved[1]);r=service.send('REBUILD_A');assert (r['A_live_pages'],r['A_submissions'],r['B_live_pages'],r['B_submissions'])==(2,0,2,0)
  r=service.send('SHUTDOWN');assert r['A_live_pages']==r['B_live_pages']==r['A_submissions']==r['B_submissions']==0
  peak=cache.peak;cache.clear();assert cache.bytes==0;service.close(True)
  def glyph(g,xy):return {'size':[g['width'],g['height']],'pixels':[x/255 for x in g['pixels']],'destination':list(xy)}
  old={'glyphs':[glyph(ro,xy) for xy in OLD]};new={'glyphs':old['glyphs']+[glyph(rf,NEW)]}
  for name,data in [('old',old),('grown',new)]:d=root/('reference-'+name);d.mkdir();(d/'reference.json').write_text(json.dumps(data))
  (root/'cpu-trace.json').write_text(json.dumps(trace,indent=2));(root/'font-receipt.json').write_text(json.dumps({'identity':provider.identity},indent=2))
  return {'cpu_peak_owned_bytes':peak,'cpu_final_owned_bytes':cache.bytes,'trace':[{k:v for k,v in t.items() if not k.endswith('_ns')} for t in trace],'events':service.events,'packed_pages':2,'packed_capacity_pixels':2*W*H,'visible_instances_before_after':[8,9],'unique_glyphs_before_after':[1,2],'overflow_no_side_effects':True}
 except BaseException:
  service.close(False)
  raise

def protocol_negative(binary,shader,root,initial,command,reason):
 service=Service(binary,shader,root)
 d=service.request_dir()
 for name in ('page0.f32','old.f32'):shutil.copyfile(initial/name,d/name)
 r=service.send('INIT');assert r['A_submissions']==1
 service.p.stdin.write(command.encode());service.p.stdin.flush();service.close(False)
 log=(root/'stdout.log').read_text()+(root/'stderr.log').read_text()
 if service.p.returncode==0 or reason not in log or log.count('COMBINED_PENDING_CLEANUP_OK')!=2:raise ValueError('protocol rejection/cleanup evidence')

def verify_events(events):
 expected=[('READY',0,0,0,0,-1),('INIT',1,1,1,0,0),('PREPARE',1,1,2,2,0),('CANCEL',1,1,2,2,0),('RELEASE_B',1,1,1,0,0),('GROW',1,1,2,0,2),('STATE',1,1,2,0,2),('STATE',1,1,2,0,2),('WRONG',1,1,2,0,2),('RELEASE_A',0,0,2,0,2),('REBUILD_A',2,0,2,0,2),('SHUTDOWN',0,0,0,0,-1)]
 if len(events)!=len(expected):raise ValueError('event count')
 for i,(r,e) in enumerate(zip(events,expected)):
  if r['seq']!=i or tuple(r[k] for k in ('op','A_live_pages','A_submissions','B_live_pages','B_submissions','B_epoch'))!=e:raise ValueError('event accounting')
  if any(not 0<=r[k]<=179224 for k in ('A_buffer_bytes','B_buffer_bytes','A_peak_buffer_bytes','B_peak_buffer_bytes')) or max(r['A_peak_submissions'],r['B_peak_submissions'])>3:raise ValueError('resource bound')
  if r['B_staging_bytes']!=(12740 if i in (2,3) else 0):raise ValueError('staging lifetime')
  if r['A_staging_bytes']!=0:raise ValueError('A steady staging')
 if any(events[-1][k] for k in ('A_buffer_bytes','B_buffer_bytes','A_staging_bytes','B_staging_bytes')):raise ValueError('remaining service buffers')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False)
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
  if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
 combined=FIX/'text_combined_lifecycle_lab';run('prepare',[sys.executable,combined/'run_lab.py','--out',out/'prepared','--font','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']);build=out/'prepared/prepared/build'
 load(HERE/'build.py','service_build').prepare(build,FIX)
 run('shader',[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2',HERE/'coverage.frag','-o',build/'shaders/coverage.frag.spv']);run('spirv',[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
 cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build),'-I'+os.environ['VULKAN_SDK_PREFIX']+'/include'];quad=load(FIX/'text_packed_quad_lab/run_lab.py','service_quad');aux=load(FIX/'font_cache_churn_lab/run_lab.py','service_aux').aux
 for name,flags in [('positive',[]),('bad-write',['-DBAD_WRITE=1'])]:run('compile-'+name,cmd+flags+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/name])
 info=exercise(build/'positive',build/'shaders',out/'positive',quad);negative=exercise(build/'bad-write',build/'shaders',out/'bad-write',quad)
 verify_events(info['events']);verify_events(negative['events'])
 corrupted=copy.deepcopy(info['events']);corrupted[3]['B_submissions']=0
 try:verify_events(corrupted)
 except ValueError as e:assert str(e)=='event accounting'
 else:raise ValueError('corrupted trace accepted')
 images={'B-initial':'old','B-old-held':'old','B-grown':'grown','A-old-released':'old','B-after-A-destroyed':'grown','A-rebuilt':'grown','B-after-A-rebuilt':'grown'};rows=[]
 for image,ref in images.items():aux(out/'positive/frames'/image);r=quad.verify(out/'positive'/('reference-'+ref),out/'positive/frames'/image);r['image']=image;rows.append(r)
 aux(out/'positive/frames/wrong-page')
 try:quad.verify(out/'positive/reference-grown',out/'positive/frames/wrong-page')
 except ValueError as e:
  if 'composition mismatch' not in str(e):raise
 else:raise ValueError('wrong page accepted')
 for image in list(images)+['wrong-page']:
  try:aux(out/'bad-write/frames'/image)
  except ValueError as e:
   if 'aux sentinel' not in str(e):raise
  else:raise ValueError('bad write accepted')
 protocol_negative(build/'positive',build/'shaders',out/'wrong-sequence',out/'positive/requests/1','PREPARE 99\n','IPC sequence')
 protocol_negative(build/'positive',build/'shaders',out/'wrong-state',out/'positive/requests/1','GROW 2\n','IPC state/opcode')
 summary=dict(trace_corruption_rejected=True,cpu_packed_payload_bytes_retained=25480,protocol_pending_cleanup_negatives=2,native_page_capacity_rejected=True,status='PASS',validation_enabled=True,positive_images=7,wrong_page_rejected=True,bad_write_rejected_images=8,active_color_attachments=3,rows=rows,**info,limits=['software Vulkan, logical offscreen devices not physical GPU/Surface','single-owner CPU service and sequential IPC; no simultaneous shader claim','fixed two-page capacity, no native heap/VRAM or arbitrary device-loss guarantee','same-provider fresh reference is transfer/composition oracle not independent typography','no crash transaction recovery between GPU commit and CPU publish'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'local-provenance.json').write_text(json.dumps({'sources':{str(p):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',HERE/'build.py',HERE/'coverage.frag',HERE/'criteria.md',FIX/'font_cache_cost_lab/cache.py',FIX/'font_cache_cost_lab/run_lab.py',HERE.parents[1]/'text_atlas_packing.py',combined/'main.cpp']},'generated':{str(p):sha(p) for p in [build/'service.hpp',build/'positive',build/'bad-write']},'prepared':json.loads((out/'prepared/local-provenance.json').read_text())},indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
