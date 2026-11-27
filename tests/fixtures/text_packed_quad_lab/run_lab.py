#!/usr/bin/env python3
"""Real glyph vertex quads with packed UVs; independent integer CPU reconstruction."""
import argparse,importlib.util,json,math,os,struct,subprocess,sys,hashlib,shutil,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];W,H=65,49

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(path,values):path.write_bytes(struct.pack('<'+'f'*len(values),*values))
def verify(out,gpu=None):
    gpu=gpu or out/'gpu';ref=json.loads((out/'reference.json').read_text());coverage=[0.]*(W*H);clipped=0
    for i,g in enumerate(ref['glyphs']):
        x,y=g['destination'];w,h=g['size']
        for q in ref['glyphs'][i+1:]:
            xx,yy=q['destination'];ww,hh=q['size']
            if not(x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y):raise ValueError('overlapping glyph destinations outside fixture scope')
    for glyph in ref['glyphs']:
        w,h=glyph['size'];dx,dy=glyph['destination'];pixels=glyph['pixels']
        for y in range(h):
            for x in range(w):
                xx,yy=dx+x,dy+y;v=pixels[y*w+x]
                if not(0<=xx<W and 0<=yy<H):clipped+=v>0;continue
                coverage[yy*W+xx]=v+coverage[yy*W+xx]*(1-v)
    def floats(name):
        b=(gpu/name).read_bytes()
        if len(b)!=W*H*16:raise ValueError('readback size')
        values=struct.unpack('<'+'f'*(W*H*4),b)
        if not all(math.isfinite(v) for v in values):raise ValueError('nonfinite readback')
        return values
    color=floats('color.rgba32f');errors=[];roi=[];outside=[]
    for i,cov in enumerate(coverage):
        a=cov*.75
        for c in range(4):
            e=abs(color[4*i+c]-((a if c==3 else (.9,.5,.2)[c]*a)+(.1,.2,.3,.5)[c]*(1-a)))
            errors.append(e);(roi if cov else outside).append(e)
    if max(errors)>1e-6:raise ValueError('quad UV composition mismatch')
    for name,expected in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
        if any(v!=expected[i%4] for i,v in enumerate(floats(name+'.rgba32f'))):raise ValueError('sentinel mismatch')
    preview=load(HERE.parent/'text_vector_lab/run_lab.py','preview')
    def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
    preview.png(gpu/'preview.png',W,H,bytes(enc(color[4*i+c]) for i in range(W*H) for c in range(3)))
    return {'glyph_quads':len(ref['glyphs']),'vertices':len(ref['glyphs'])*6,'max_linear_error':max(errors),'max_roi_error':max(roi),'max_background_error':max(outside),'clipped_nonzero_source_pixels':clipped,'roi_pixels':sum(v>0 for v in coverage),'tolerance':1e-6,'sentinels':'UNCHANGED'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args,expected=0):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);text=r.stdout+r.stderr;(out/(name+'.log')).write_text(text)
        if r.returncode!=expected or 'VALIDATION:' in text:raise RuntimeError(name+' failed')
        return text
    bitmap=load(HERE.parent/'text_bitmap_lab/run_lab.py','bitmap');sys.path.insert(0,str(ROOT/'tests'))
    try:from text_atlas_packing import ShelfAtlas
    finally:sys.path.pop(0)
    glyphs=[];rectangles=[];receipts=[]
    for letter,dest in [('O',(-2,4)),('f',(25,13)),('i',(49,30))]:
        mask,receipt=bitmap.raster(a.font,letter,'ltr','en');receipts.append(receipt)
        xy=[(i%W,i//W) for i,c in enumerate(mask) if c];x0=min(x for x,y in xy);x1=max(x for x,y in xy)+1;y0=min(y for x,y in xy);y1=max(y for x,y in xy)+1
        w,h=x1-x0,y1-y0;pixels=[mask[y*W+x] for y in range(y0,y1) for x in range(x0,x1)]
        glyphs.append(dict(letter=letter,size=[w,h],pixels=pixels,destination=list(dest)));rectangles.append((w,h,pixels))
    atlas=ShelfAtlas(W,H,padding=1,max_pages=1);places=atlas.publish(atlas.prepare(rectangles));page=atlas.snapshot()[0];vertices=[]
    for glyph,loc in zip(glyphs,places):
        w,h=glyph['size'];dx,dy=glyph['destination'];glyph['atlas_rect']=[loc.x,loc.y,w,h]
        for x,y in [(0,0),(w,0),(0,h),(0,h),(w,0),(w,h)]:vertices.extend([2*(dx+x)/W-1,2*(dy+y)/H-1,(loc.x+x)/W,(loc.y+y)/H])
    raw(out/'atlas.f32',page);raw(out/'vertices.f32',vertices);(out/'reference.json').write_text(json.dumps({'glyphs':glyphs})+'\n');(out/'provider-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    base=HERE.parent/'text_vector_lab';build=out/'build';run('base-build',[base/'build.sh',build])
    run('vertex-compile',[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',HERE/'quad.vert','-o',build/'shaders/fullscreen.vert.spv'])
    run('vertex-validate',[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',build/'shaders/fullscreen.vert.spv'])
    def replace_once(text,old,new):
        if text.count(old)!=1:raise ValueError('reused source hook changed: '+old)
        return text.replace(old,new)
    source=(base/'main.cpp').read_text()
    source=replace_once(source,'int main(int argc,char** argv)','int old_vector_main(int argc,char** argv)')
    source=replace_once(source,'../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'))
    source=replace_once(source,'struct TextLab: Vulkan {','struct TextLab: Vulkan {\n size_t quadBuffer=0;uint32_t quadCount=0;')
    old='VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};'
    source=replace_once(source,old,old+'VkVertexInputBindingDescription bind{0,16,VK_VERTEX_INPUT_RATE_VERTEX};VkVertexInputAttributeDescription attrs[2]={{0,0,VK_FORMAT_R32G32_SFLOAT,0},{1,0,VK_FORMAT_R32G32_SFLOAT,8}};vi.vertexBindingDescriptionCount=1;vi.pVertexBindingDescriptions=&bind;vi.vertexAttributeDescriptionCount=2;vi.pVertexAttributeDescriptions=attrs;')
    source=replace_once(source,'begin();barrier(', 'begin();barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT);barrier(')
    source=replace_once(source,'vkCmdDraw(cb,3,1,0,0);','VkDeviceSize offset=0;vkCmdBindVertexBuffers(cb,0,1,&buffers[quadBuffer].buffer,&offset);vkCmdDraw(cb,quadCount,1,0,0);')
    if source.count('vkCmdDraw(cb,quadCount')!=1:raise ValueError('hook changed')
    (build/'quad_lab_reused.hpp').write_text(source)
    cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
    if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',cmd+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'quad_lab'])
    tools={}
    for key,default in [('CXX','g++'),('GLSLANG','glslangValidator'),('SPIRV_VAL','spirv-val')]:
        resolved=shutil.which(os.environ.get(key,default))
        if not resolved:raise ValueError('missing tool '+key)
        tools[key]={'sha256':sha(Path(resolved)),'version':run('version-'+key,[resolved,'--version'])}
    drivers={}
    for name in os.environ.get('VK_DRIVER_FILES','').split(os.pathsep):
        if not name:continue
        path=Path(name);drivers[str(path)]=sha(path)
        lib=Path(json.loads(path.read_text())['ICD']['library_path'])
        if lib.is_absolute() and lib.is_file():drivers[str(lib)]=sha(lib)
    layers={}
    for name in os.environ.get('VK_LAYER_PATH','').split(os.pathsep):
        if name:
            for path in Path(name).glob('*.json'):layers[str(path)]=sha(path)
    receipt={'tools':tools,'driver_hashes':drivers,'validation_manifests':layers,'platform':platform.platform(),'tests_revision':run('tests-head',['git','rev-parse','HEAD','HEAD^{tree}']),'tests_status':run('tests-status',['git','status','--porcelain']),'binary_sha256':sha(build/'quad_lab'),'generated_helper_hashes':{p.name:sha(p) for p in [build/'quad_lab_reused.hpp']}}
    if os.environ.get('VULKAN_SKILL_ROOT'):receipt['skill_revision']=run('skill-head',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
    (out/'local-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    log=run('vulkan',[build/'quad_lab',build/'shaders',out/'atlas.f32',out/'vertices.f32',out/'gpu'])
    if 'validation_enabled=1' not in log:raise ValueError('validation required')
    result=verify(out)
    wrong=vertices.copy()
    for i in range(2,len(wrong),4):wrong[i]+=1/W
    raw(out/'wrong-uv.f32',wrong);run('wrong-uv-draw',[build/'quad_lab',build/'shaders',out/'atlas.f32',out/'wrong-uv.f32',out/'wrong-gpu'])
    try:verify(out,out/'wrong-gpu')
    except ValueError:pass
    else:raise ValueError('wrong UV undetected')
    invalid=vertices.copy();invalid[2]=2;raw(out/'invalid.f32',invalid)
    run('reject-vertex',[build/'quad_lab',build/'shaders',out/'atlas.f32',out/'invalid.f32',out/'invalid-gpu'],1)
    if (out/'invalid-gpu').exists():raise ValueError('bad input reached GPU')
    summary={'status':'PASS','validation_enabled':True,'numeric':result,'negative_checks':['actual one-texel UV shift rejected by independent reference','out-of-range UV rejected before GPU'],'scope':'real font coverage packed into atlas; actual vertex quad UV draws with integer 1:1 nearest sampling','unverified':['fractional scale/filtering','full text shaping layout','MSDF','target platforms','performance']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'source-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in [HERE/'main.cpp',HERE/'quad.vert',HERE/'run_lab.py',base/'main.cpp',ROOT/'tests/text_atlas_packing.py',HERE.parent/'text_bitmap_lab/run_lab.py',ROOT/'tests/platform_text_probe.py',base/'coverage.frag',base/'build.sh',HERE.parent/'engine_scale_lab/main.cpp']},indent=2)+'\n');print(json.dumps(summary));return 0
if __name__=='__main__':raise SystemExit(main())
