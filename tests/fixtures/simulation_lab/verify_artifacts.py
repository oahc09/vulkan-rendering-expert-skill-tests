#!/usr/bin/env python3
"""Independent readback/identity verifier. Thresholds are fixed in source."""
import hashlib,importlib.util,json,math,sys
from pathlib import Path

WATER=[(17,b,e) for b in range(3) for e in (2,0)]+[(17,1,1),(17,1,3),(9,1,2)]
def require(ok,why):
    if not ok:raise ValueError(why)
def load(path):return json.loads(path.read_text())
def error(a,b):
    require(len(a)==len(b),'array shape')
    return max((abs(x-y) for x,y in zip(a,b)),default=0.)
def flat(a):return [v for row in a for v in row]
def verify(root,strict=True):
    root=Path(root);manifest=load(root/'manifest.json');summary=load(root/'result.json')
    require(manifest['layer']=='VulkanIntegration' and manifest['exit_code']==0,'execution failed')
    if strict:require(not manifest['tests_dirty'] and not manifest['skill_dirty'],'dirty source')
    require(manifest['device'] and manifest['device'][0]['validation']==1,'validation unavailable')
    require(summary['status']=='PASS' and summary['validation_errors']==0 and summary['validation_available']==1,'validation error')
    require(not summary['float_atomics_enabled'] and summary['mobile_acceptance']=='UNVERIFIED','scope')
    for name,digest in manifest['files'].items():
        require(Path(name).name==name,'invalid filename')
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'artifact hash '+name)
    require(set(manifest['files'])=={p.name for p in root.iterdir() if p.is_file() and p.name!='manifest.json'},'unbound output files')
    build=load(root/'build-manifest.json');require(build['tests_sha']==manifest['tests_sha'],'mixed build/run source')
    spec=importlib.util.spec_from_file_location('simulation_build_manifest',Path(__file__).with_name('build_manifest.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    require(build['sources']==mod.source_files(Path(__file__).resolve().parent),'source changed since build')
    require(len(build['artifacts'])==16 and len(build['sources'])>=20,'build closure')
    names={f'{kind}-{method}':(2,1,1,False) for kind in ('hard','soft') for method in ('colored','jacobi')}
    names.update({f'{kind}-{method}-tick{tick}':(8 if kind=='cloth' else 32,8 if kind=='cloth' else 1,tick,False) for kind in ('cloth','rope') for method in ('colored','jacobi') for tick in range(1,9)})
    names.update({f'wave-{n}-{b}-events{e}-tick{tick}':(n,n,tick,True) for n,b,e in WATER for tick in range(12)})
    require(summary['numerical_cases']==len(names)==144 and summary['draws']==52,'matrix size')
    maximum=0.;normal_max=0.;bounds_max=0.;residual_max=0.
    for name,(nx,ny,tick,water) in names.items():
        data=load(root/(name+'.json'));n=nx*ny;tol=5e-5 if name.startswith(('rope','cloth')) else 1e-5
        require(data['name']==name and data['tick']==tick and data['tolerance']==tol and data['normal_tolerance']==5e-5,'case identity/tolerance')
        for key,stride in [('cpu',3),('gpu',3),('normals',4),('cpu_normals',3)]:
            require(len(data[key])==n and all(len(row)==stride for row in data[key]),key+' shape')
            require(all(math.isfinite(x) for x in flat(data[key])),key+' finite')
        actual=error(flat(data['cpu']),flat(data['gpu']));require(actual<=tol and abs(data['max_error']-actual)<1e-14,'position/velocity error')
        maximum=max(maximum,actual);norm_error=error(flat(data['cpu_normals']),[v for row in data['normals'] for v in row[:3]])
        require(norm_error<=5e-5 and abs(norm_error-data['normal_max_error'])<1e-14,'normal error');normal_max=max(normal_max,norm_error)
        require(all(row[3]==tick for row in data['normals']),'normal generation')
        for i in range(n):
            x,y=i%nx,i//nx;l=y*nx+max(x-1,0);r=y*nx+min(x+1,nx-1);d=max(y-1,0)*nx+x;u=min(y+1,ny-1)*nx+x
            normal=[0.,0.,1.]
            if water:normal=[-(data['cpu'][r][0]-data['cpu'][l][0])/(r-l)*(nx-1),-(data['cpu'][u][0]-data['cpu'][d][0])/((u-d)/nx)*(ny-1),1.]
            elif ny>1:
                a=[data['cpu'][r][c]-data['cpu'][l][c] for c in range(3)];b=[data['cpu'][u][c]-data['cpu'][d][c] for c in range(3)]
                normal=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
            length=math.hypot(*normal);normal=[v/length for v in normal] if length>1e-8 else [0.,0.,1.]
            require(error(normal,data['cpu_normals'][i])<1e-13,'CPU normal oracle')

        pos=[(i%nx/(nx-1),i//nx/(ny-1),row[0]) if water else row for i,row in enumerate(data['cpu'])]
        bounds=[min(row[c] for row in pos) for c in range(3)]+[tick]+[max(row[c] for row in pos) for c in range(3)]+[tick]
        require(error(bounds,data['cpu_bounds'])<1e-14,'CPU bounds oracle')
        be=error(bounds,data['bounds']);require(be<=tol and data['bounds'][3]==data['bounds'][7]==tick,'GPU bounds');bounds_max=max(bounds_max,be)
        if name.startswith(('cloth','rope')):
            con=load(root/(name+'-constraints.json'));require(con['residual_difference_tolerance']==1e-4 and con['lambda_tolerance']==5e-5 and con['penetration_tolerance']==1e-5 and con['fixed_tolerance']==0,'constraint tolerance')
            re=0.;le=0.
            for a,b,rest,cr,gr,cl,gl in con['edges']:
                require(type(a)==int and type(b)==int and 0<=a<n and 0<=b<n and a!=b,'edge')
                cpu=math.dist(data['cpu'][a],data['cpu'][b])-rest;gpu=math.dist(data['gpu'][a],data['gpu'][b])-rest
                require(abs(cpu-cr)<1e-14 and abs(gpu-gr)<1e-14,'residual oracle');re=max(re,abs(cpu-gpu));le=max(le,abs(cl-gl))
            fixed={0,7} if name.startswith('cloth') else {0};penetration=0.;fixed_error=0.
            for i,g in enumerate(data['gpu']):
                if i in fixed:fixed_error=max(fixed_error,math.dist(g,data['cpu'][i]))
                else:
                    center=[max(-.18,min(.18,g[0])) if name.startswith('cloth') else 0.,-.2,0.]
                    penetration=max(penetration,-.55-g[1],.14-math.dist(g,center))
            require(re<=1e-4 and le<=5e-5 and penetration<=1e-5 and fixed_error==0,'constraint error')
            require(abs(re-con['max_residual_difference'])<1e-14 and abs(le-con['max_lambda_error'])<1e-14 and abs(penetration-con['max_discrete_penetration'])<1e-14,'constraint report mismatch');residual_max=max(residual_max,re)
    require(abs(summary['max_position_or_velocity_error']-maximum)<1e-14,'summary maximum')
    images=list(root.glob('*.rgba'));require(len(images)==52,'draw count')
    for path in images:
        raw=path.read_bytes();require(len(raw)==65*49*4 and any(raw[i] for i in range(len(raw)) if i%4<3),'image coverage')
    times=[json.loads(line) for line in (root/'timings.jsonl').read_text().splitlines()]
    require(len(times)==196 and sum(row['phase']=='tick' for row in times)==144,'timing count')
    for row in times:
        require(math.isfinite(row['cpu_record_submit_wait_ms']) and row['cpu_record_submit_wait_ms']>=0,'CPU timing')
        require(not row['hardware_performance_claim'],'timing scope')
        require(len(row['gpu_stage_ms']) in (0,2) and all(math.isfinite(x) and x>=0 for x in row['gpu_stage_ms']),'GPU timing')
    return dict(status='PASS',numerical_cases=144,draws=52,max_position_or_velocity_error=maximum,max_normal_error=normal_max,max_bounds_error=bounds_max,max_residual_difference=residual_max,shader_artifacts=15,android='UNVERIFIED')
if __name__=='__main__':print(json.dumps(verify(sys.argv[1],strict='--allow-dirty' not in sys.argv),indent=2))
