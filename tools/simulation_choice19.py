"""Recompute bounded existing lab quality; not a third independent trajectory solver."""
import math,struct
SCENES=('rope','cloth');METHODS=('colored','jacobi')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def number(x):return type(x)in(int,float) and abs(x)<1e100 and math.isfinite(x)
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def expected_edges(scene):
 w,h=(8,8) if scene=='cloth' else (32,1);pairs=[]
 for y in range(h):
  for x in range(w):
   i=y*w+x
   if x+1<w:pairs.append((i,i+1))
   if y+1<h:pairs.append((i,i+w))
   if scene=='cloth' and x+1<w and y+1<h:pairs.extend([(i,i+w+1),(i+1,i+w)])
   if scene=='cloth' and x+2<w:pairs.append((i,i+2))
   if scene=='cloth' and y+2<h:pairs.append((i,i+2*w))
 colors=[];used=[]
 for a,b in pairs:
  ci=next((i for i,u in enumerate(used) if a not in u and b not in u),len(used))
  if ci==len(used):used.append(set());colors.append([])
  used[ci].update((a,b));colors[ci].append((a,b))
 return [p for color in colors for p in color]
def initial(scene,i):
 if scene=='cloth':return [f32(f32(-.42)+f32(f32(.12)*(i%8))),f32(f32(.45)-f32(f32(.12)*(i//8))),0.]
 return [f32(f32(-.62)+f32(f32(.04)*i)),f32(.12),0.]
def analyze(snapshots):
 require(type(snapshots)is list and len(snapshots)==32,'32 snapshots required')
 seen=set();results={s:{m:dict(max_absolute_residual=0.,max_penetration=0.,max_cpu_match_error=0.,ticks=[]) for m in METHODS} for s in SCENES};edge_defs={}
 for packet in snapshots:
  require(type(packet)is dict and set(packet)=={'scene','method','tick','state','constraints'},'packet schema')
  scene,method,tick=packet['scene'],packet['method'],packet['tick'];require(scene in SCENES and method in METHODS and type(tick)is int and 1<=tick<=8,'scope');key=scene,method,tick;require(key not in seen,'duplicate snapshot');seen.add(key)
  d,c=packet['state'],packet['constraints'];require(type(d)is dict and type(c)is dict,'raw records');n=64 if scene=='cloth' else 32
  require(d['name']==f'{scene}-{method}-tick{tick}' and type(d['tick'])is int and d['tick']==tick and d['tolerance']==5e-5 and d['normal_tolerance']==5e-5,'identity/threshold')
  for k,width in [('cpu',3),('gpu',3),('normals',4),('cpu_normals',3)]:require(type(d[k])is list and len(d[k])==n and all(type(row)is list and len(row)==width and all(number(x) for x in row) for row in d[k]),'state shape/finite')
  error=max(abs(a-b) for ca,ga in zip(d['cpu'],d['gpu']) for a,b in zip(ca,ga));require(error<=5e-5 and number(d['max_error']) and abs(error-d['max_error'])<1e-14,'CPU match')
  normal_error=0.
  for i in range(n):
   normal=[0.,0.,1.]
   if scene=='cloth':
    x,y=i%8,i//8;left=y*8+max(0,x-1);right=y*8+min(7,x+1);down=max(0,y-1)*8+x;up=min(7,y+1)*8+x
    a=[d['cpu'][right][k]-d['cpu'][left][k] for k in range(3)];b=[d['cpu'][up][k]-d['cpu'][down][k] for k in range(3)];normal=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];length=math.hypot(*normal);normal=[v/length for v in normal] if length>1e-8 else [0.,0.,1.]
   require(max(abs(a-b) for a,b in zip(normal,d['cpu_normals'][i]))<1e-13,'independent normal');normal_error=max(normal_error,max(abs(a-b) for a,b in zip(normal,d['normals'][i][:3])))
  require(normal_error<=5e-5 and number(d['normal_max_error']) and abs(normal_error-d['normal_max_error'])<1e-14,'normal metric')
  require(all(row[3]==tick for row in d['normals']) and len(d['bounds'])==8 and all(number(x) for x in d['bounds']) and d['bounds'][3]==d['bounds'][7]==tick,'generation')
  bounds=[min(row[k] for row in d['cpu']) for k in range(3)]+[tick]+[max(row[k] for row in d['cpu']) for k in range(3)]+[tick];require(max(abs(a-b) for a,b in zip(bounds,d['bounds']))<=5e-5,'bounds')
  require(all(c[k]==v and number(c[k]) for k,v in {'residual_difference_tolerance':1e-4,'lambda_tolerance':5e-5,'penetration_tolerance':1e-5,'fixed_tolerance':0}.items()),'unchanged tolerances')
  ordered_edges=expected_edges(scene);expected=set(ordered_edges);require(type(c['edges'])is list and len(c['edges'])==len(expected),'complete edges');pairs=set();defs=[];absolute=diff=lam=0.
  for edge in c['edges']:
   require(type(edge)is list and len(edge)==7,'edge shape');a,b,rest,cr,gr,cl,gl=edge
   require(type(a)is int and type(b)is int and (a,b)in expected and (a,b)not in pairs,'edge identity/duplicate');pairs.add((a,b));require(all(number(v) for v in edge[2:]) and rest>0,'edge numbers')
   # Frozen initial FP32 coordinates and float rest construction; allow only
   # float expression rounding, not a caller-invented rest length.
   ia,ib=initial(scene,a),initial(scene,b);dx=f32(ia[0]-ib[0]);dy=f32(ia[1]-ib[1]);expected_rest=f32(math.sqrt(f32(f32(dx*dx)+f32(dy*dy))));require(rest==expected_rest,'rest definition')
   cpu=math.dist(d['cpu'][a],d['cpu'][b])-rest;gpu=math.dist(d['gpu'][a],d['gpu'][b])-rest
   require(abs(cpu-cr)<1e-14 and abs(gpu-gr)<1e-14,'raw residual');absolute=max(absolute,abs(gpu));diff=max(diff,abs(cpu-gpu));lam=max(lam,abs(cl-gl));defs.append((a,b,rest))
  require(pairs==expected and [(e[0],e[1]) for e in c['edges']]==ordered_edges,'edge set/order')
  if scene in edge_defs:require(defs==edge_defs[scene],'mixed constraints')
  edge_defs[scene]=defs
  fixed={0,7} if scene=='cloth' else {0};penetration=0.;fixed_error=0.
  for i,g in enumerate(d['gpu']):
   if i in fixed:fixed_error=max(fixed_error,math.dist(g,d['cpu'][i]))
   else:
    center=[max(-.18,min(.18,g[0])) if scene=='cloth' else 0.,-.2,0.];penetration=max(penetration,-.55-g[1],.14-math.dist(g,center))
  for k,v in dict(max_absolute_residual_observed=absolute,max_residual_difference=diff,max_lambda_error=lam,max_discrete_penetration=penetration,max_fixed_error=fixed_error).items():require(number(c[k]) and abs(v-c[k])<1e-14,'recomputed '+k)
  require(diff<=1e-4 and lam<=5e-5 and penetration<=1e-5 and fixed_error==0,'original numerical gates')
  r=results[scene][method];r['max_absolute_residual']=max(r['max_absolute_residual'],absolute);r['max_penetration']=max(r['max_penetration'],penetration);r['max_cpu_match_error']=max(r['max_cpu_match_error'],error);r['ticks'].append(tick)
 require(seen=={(s,m,t) for s in SCENES for m in METHODS for t in range(1,9)},'snapshot set')
 for scene in results.values():
  for r in scene.values():r['ticks'].sort()
 return results

def decide(snapshots,policy):
 base=dict(rule_id='C2.simulation.fixed-lab19',version_scope='original sim16 source with frozen numerical thresholds',alternatives=list(METHODS),revisit_conditions=['workload/constraints/time-step/cohort changes','product quality targets or target-device performance evidence'],limitations=['C++ FP64 trajectory reference per algorithm; Python recomputes metrics, not a full trajectory.','Algorithms are not convergence-equivalent; CPU match error is not product residual.','Synchronous CPU ICD; no physical/mobile/async performance.'])
 try:
  metrics=analyze(snapshots);require(type(policy)is dict and set(policy)=={'baseline','quality_targets','require_performance'},'policy schema');baseline=policy['baseline'];require(baseline in METHODS and type(policy['require_performance'])is bool,'policy');targets=policy['quality_targets']
  if targets is None:return dict(base,status='NEEDS_QUALITY_TARGET',selected=None,fallback=baseline,metrics=metrics)
  require(type(targets)is dict and set(targets)==set(SCENES),'product target scenes')
  for q in targets.values():require(type(q)is dict and set(q)=={'max_absolute_residual','max_penetration'} and all(number(v) and v>=0 for v in q.values()),'product quality target')
  eligible=[m for m in METHODS if all(metrics[s][m][k]<=targets[s][k] for s in SCENES for k in targets[s])]
  if not eligible:return dict(base,status='NO_QUALITY_ADMISSIBLE_PATH',selected=None,eligible=eligible,metrics=metrics)
  if policy['require_performance']:return dict(base,status='NEEDS_MEASUREMENT',selected=None,fallback=baseline if baseline in eligible else None,eligible=eligible,metrics=metrics)
  return dict(base,status='KEEP_BASELINE' if baseline in eligible else 'QUALITY_ADMISSIBLE_ALTERNATIVE',selected=baseline if baseline in eligible else eligible[0],eligible=eligible,metrics=metrics)
 except (ValueError,TypeError,KeyError,OverflowError):return dict(base,status='UNKNOWN',selected=None)
