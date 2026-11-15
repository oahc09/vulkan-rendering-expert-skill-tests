"""Generated bounded CPU path masks through actual Vulkan, not GPU tessellation."""
import importlib.util,json,struct,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run_cases(build,out):
    raster=load(ROOT/'tests/bounded_vector_mask.py','bounded_path')
    verify=load(HERE/'run_lab.py','bitmap_oracle').verify
    outer=[('M',12,6),('L',53,6),('L',53,43),('L',12,43),('Z',)]
    inner=[('M',22,16),('L',43,16),('L',43,33),('L',22,33),('Z',)]
    reverse=[('M',22,16),('L',22,33),('L',43,33),('L',43,16),('Z',)]
    quad=[('M',10,30),('Q',25,4,50,30),('L',50,40),('L',10,40),('Z',)]
    cubic=[('M',10,30),('C',15,4,45,4,50,30),('L',50,40),('L',10,40),('Z',)]
    cases=[('path-evenodd',[outer,inner],{'fill':'evenodd'}),('path-nonzero',[outer,reverse],{}),('path-quad',[quad],{}),('path-cubic',[cubic],{}),('path-negative',[outer,reverse],{'transform':(-1,0,0,1,65,0)})]
    rows=[]
    for name,paths,options in cases:
        folder=out/name;folder.mkdir(exist_ok=False)
        mask=raster.coverage(paths,65,49,**options)
        if 'quad' not in name and 'cubic' not in name:
            # Independent integer rectangle area and hole/stroke checks.
            assert sum(mask)==41*37-21*17
            assert mask[24*65+32]==0 and mask[24*65+16]==1
        (folder/'mask.f32').write_bytes(struct.pack('<'+'f'*len(mask),*mask))
        (folder/'path.json').write_text(json.dumps({'commands':paths,'options':options,'tolerance_pixels':.125,'samples':4})+'\n')
        result=subprocess.run([str(build/'bitmap_lab'),str(build/'shaders'),str(folder/'mask.f32'),str(folder/'gpu')],capture_output=True,text=True,timeout=120)
        log=result.stdout+result.stderr;(out/(name+'.log')).write_text(log)
        if result.returncode or 'VALIDATION:' in log or 'validation_enabled=1' not in log:raise RuntimeError('vector GPU failure')
        row=verify(folder);row.update(case=name,validation_enabled=True,reference='CPU bounded mask -> independent linear GPU-composition oracle',path_edges=sum(len(p)-1 for p in raster.flatten(paths,**{k:v for k,v in options.items() if k!='fill'})))
        rows.append(row)
    return rows
