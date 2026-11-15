#!/usr/bin/env python3
"""Bounded bitmap quad scale/quarter-turn experiment, not font quality certification."""
import argparse,hashlib,importlib.util,json,math,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49
# Fixed before measurements. This is exact nearest reconstruction, not a
# typography similarity threshold or permission to relax failing cases.
CASES=[('half',.5,0,20.25,15.25),('unit',1.,0,20.25,15.25),('large',1.5,0,20.25,15.25),('quarter-turn',1.5,90,40.25,8.25)]
PIXEL_TOLERANCE=1e-6;AREA_TOLERANCE=1e-3

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path,n):
    b=path.read_bytes()
    if len(b)!=n*4:raise ValueError('readback size')
    a=struct.unpack('<'+'f'*n,b)
    if not all(math.isfinite(v) for v in a):raise ValueError('nonfinite readback')
    return a

def expected(ref,case):
    _,scale,angle,dx,dy=case;w,h=ref['size'];pixels=ref['pixels'];result=[]
    for y in range(H):
        for x in range(W):
            # Inverse local coordinates from destination sample centers, not
            # GPU vertex/UV buffers. Only exact quarter-turn transforms allowed.
            a=(x+.5-dx)/scale;b=(y+.5-dy)/scale
            sx,sy=(a,b) if angle==0 else (b,-a)
            result.append(pixels[math.floor(sy)*w+math.floor(sx)] if 0<=sx<w and 0<=sy<h else 0.)
    return result

def verify(out,gpu=None,case_name=None):
    if case_name is not None and case_name not in {c[0] for c in CASES}:raise ValueError('unknown affine case')
    ref=json.loads((out/'glyph-reference.json').read_text());rows=[]
    for case in CASES:
        name,scale,angle,_,_=case
        if case_name and name!=case_name:continue
        folder=gpu or out/name;cov=expected(ref,case);color=read(folder/'color.rgba32f',W*H*4);errors=[];roi=[]
        for i,c in enumerate(cov):
            a=c*.75
            for k in range(4):
                reference=(a if k==3 else (.9,.5,.2)[k]*a)+(.1,.2,.3,.5)[k]*(1-a)
                err=abs(color[4*i+k]-reference);errors.append(err)
                if c:roi.append(err)
        if max(errors)>PIXEL_TOLERANCE:raise ValueError('affine nearest composition mismatch')
        for file,values in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
            if any(v!=values[i%4] for i,v in enumerate(read(folder/(file+'.rgba32f'),W*H*4))):raise ValueError('sentinel changed')
        area=sum(cov);gpu_area=sum((color[4*i+3]-.5)/.375 for i in range(W*H))
        if abs(area-gpu_area)>AREA_TOLERANCE:raise ValueError('coverage area mismatch')
        normalized=area/(scale*scale);original=sum(ref['pixels'])
        rows.append(dict(case=name,scale=scale,rotation_degrees=angle,roi_pixels=sum(c>0 for c in cov),max_linear_error=max(errors),max_roi_error=max(roi),coverage_area_error=abs(area-gpu_area),normalized_area_change=normalized/original-1,pixel_tolerance=PIXEL_TOLERANCE,area_tolerance=AREA_TOLERANCE))
        preview=load(HERE.parent/'text_vector_lab/run_lab.py','affine_preview')
        def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
        preview.png(folder/'preview.png',W,H,bytes(enc(color[4*i+c]) for i in range(W*H) for c in range(3)))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--font',required=True,type=Path);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args,code=0):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
        if r.returncode!=code or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
        return log
    quad=HERE.parent/'text_packed_quad_lab';run('prepare',[sys.executable,quad/'run_lab.py','--out',out/'prepared','--font',a.font]);prepared=out/'prepared';build=prepared/'build'
    ref=json.loads((prepared/'reference.json').read_text())['glyphs'][0];(out/'glyph-reference.json').write_text(json.dumps(ref)+'\n');w,h=ref['size'];ax,ay,_,_=ref['atlas_rect'];buffers={}
    for case in CASES:
        name,scale,angle,dx,dy=case;vertices=[]
        for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:
            xx,yy=(x,y) if angle==0 else (-y,x);vertices.extend([2*(dx+scale*xx)/W-1,2*(dy+scale*yy)/H-1,(ax+x)/W,(ay+y)/H])
        path=out/(name+'.vertices.f32');path.write_bytes(struct.pack('<24f',*vertices));buffers[name]=vertices
        log=run('draw-'+name,[build/'quad_lab',build/'shaders',prepared/'atlas.f32',path,out/name])
        if 'validation_enabled=1' not in log:raise ValueError('validation required')
    rows=verify(out)
    wrong=buffers['half'].copy()
    for i in range(2,len(wrong),4):wrong[i]+=1/W
    path=out/'wrong.vertices.f32';path.write_bytes(struct.pack('<24f',*wrong));run('wrong-uv',[build/'quad_lab',build/'shaders',prepared/'atlas.f32',path,out/'wrong'])
    try:verify(out,out/'wrong','half')
    except ValueError as e:
        if 'composition mismatch' not in str(e):raise
    else:raise ValueError('wrong UV not rejected')
    summary={'status':'PASS','validation_enabled':True,'cases':rows,'negative_checks':['actual valid wrong UV draw rejected'],'scope':'actual packed bitmap O quad at half/unit/1.5 scale and90-degree rotation; exact nearest pixel-center reconstruction','quality_caveat':'normalized coverage-area change is aliasing diagnostic, NOT a font-quality acceptance gate; no optimal filtering claim','unverified':['arbitrary-angle/perspective','MSDF/color/variable fonts','temporal transforms','typographic quality','target devices/performance']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'local-provenance.json').write_text(json.dumps({'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'run_lab.py',quad/'run_lab.py',quad/'main.cpp',quad/'quad.vert']},'prepared_tool_driver_receipt':json.loads((prepared/'local-provenance.json').read_text())},indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
