#!/usr/bin/env python3
import argparse,hashlib,json,math,os,struct,subprocess,shutil,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('source hook changed: '+old)
    return text.replace(old,new)
def verify(folder):
    def f(name,n):
        b=(folder/(name+'.f32')).read_bytes()
        if len(b)!=n*4:raise ValueError('readback size')
        a=struct.unpack('<'+'f'*n,b)
        if not all(math.isfinite(x) for x in a):raise ValueError('nonfinite')
        return a
    color=f('color',65*49*4);error=max(abs(v-(1 if i%4==3 else .52)) for i,v in enumerate(color))
    if error>1e-6:raise ValueError('color mismatch')
    for name,expected in [('velocity',(.125,-.25,.5,1)),('id',(37,91,12,1))]:
        if any(v!=expected[i%4] for i,v in enumerate(f(name,65*49*4))):raise ValueError('active MRT sentinel changed')
    if any(v!=.375 for v in f('depth',65*49)):raise ValueError('depth sentinel changed')
    return {'max_color_error':error,'tolerance':1e-6,'velocity_id_unchanged_pixels':3185,'depth_unchanged_pixels':3185}
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    def run(name,args):
        r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,timeout=120);log=r.stdout+r.stderr;(out/(name+'.log')).write_text(log)
        if r.returncode or 'VALIDATION:' in log:raise RuntimeError(name+' failed')
        return log
    base=HERE.parent/'text_vector_lab';build=out/'build';run('base-build',[base/'build.sh',build])
    run('shader',[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',HERE/'active.frag','-o',build/'shaders/coverage.frag.spv'])
    run('spirv',[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',build/'shaders/coverage.frag.spv'])
    engine=HERE.parent/'engine_scale_lab/main.cpp';helper=replace(engine.read_text(),'enabled.multiDrawIndirect = mdi;','enabled.multiDrawIndirect = mdi;\nif(!f2.features.independentBlend)throw std::runtime_error("independentBlend unavailable");enabled.independentBlend=VK_TRUE;')
    (build/'engine_active.hpp').write_text(helper)
    s=(base/'main.cpp').read_text();s=replace(s,'../engine_scale_lab/main.cpp',str(build/'engine_active.hpp'));s=replace(s,'int main(int argc,char** argv)','int unused_vector_main(int argc,char** argv)')
    s=replace(s,'struct TextLab: Vulkan {','static bool gBadMask=false,gBadDepth=false;\nstruct TextLab: Vulkan {\n Image depth;size_t readDepth;')
    s=replace(s,'    upload=buffers.size();', '''    vkGetPhysicalDeviceFormatProperties(physical,VK_FORMAT_D32_SFLOAT,&props);
    VkFormatFeatureFlags depthNeed=VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
    if((props.optimalTilingFeatures&depthNeed)!=depthNeed)throw std::runtime_error("D32 transfer/depth unsupported");
    depth=image(VK_FORMAT_D32_SFLOAT,VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);
    readDepth=buffers.size();buffers.push_back(buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    upload=buffers.size();''')
    s=replace(s,'VkAttachmentDescription attachments[3]{};','VkAttachmentDescription attachments[4]{};')
    s=replace(s,'VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}};', 'attachments[3].format=VK_FORMAT_D32_SFLOAT;attachments[3].initialLayout=attachments[3].finalLayout=VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;VkAttachmentReference dr{3,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{1,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{2,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}};')
    s=replace(s,'sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;','sub.pDepthStencilAttachment=&dr;')
    s=replace(s,'rp.attachmentCount=3;','rp.attachmentCount=4;');s=replace(s,'VkImageView views[]={target.view,velocity.view,ids.view};','VkImageView views[]={target.view,velocity.view,ids.view,depth.view};');s=replace(s,'fb.attachmentCount=3;','fb.attachmentCount=4;')
    s=replace(s,'VkPipelineColorBlendStateCreateInfo bs{','for(int i=1;i<3;i++){blends[i].blendEnable=VK_FALSE;blends[i].colorWriteMask=gBadMask?15:0;}VkPipelineDepthStencilStateCreateInfo ds{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};ds.depthTestEnable=VK_TRUE;ds.depthWriteEnable=gBadDepth;ds.depthCompareOp=VK_COMPARE_OP_ALWAYS;\n    VkPipelineColorBlendStateCreateInfo bs{')
    s=replace(s,'pi.pColorBlendState=&bs;','pi.pColorBlendState=&bs;pi.pDepthStencilState=&ds;')
    s=replace(s,'    VkRenderPassBeginInfo rp{', '''    transition(depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,0,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);
    VkClearDepthStencilValue dv{.375f,0};VkImageSubresourceRange depthRange{VK_IMAGE_ASPECT_DEPTH_BIT,0,1,0,1};vkCmdClearDepthStencilImage(cb,depth.image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,&dv,1,&depthRange);
    transition(depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT);
    VkRenderPassBeginInfo rp{''')
    s=replace(s,'    barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);submit();', '''    transition(depth,VK_IMAGE_ASPECT_DEPTH_BIT,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);copyImage(depth,VK_IMAGE_ASPECT_DEPTH_BIT,buffers[readDepth]);
    barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);submit();''')
    s=replace(s,'for(auto im:{target,velocity,ids,coverage})','for(auto im:{target,velocity,ids,coverage,depth})');(build/'active_lab_reused.hpp').write_text(s)
    cmd=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(build)]
    if os.environ.get('VULKAN_SDK_PREFIX'):cmd+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
    run('compile',cmd+[HERE/'main.cpp','-l:libvulkan.so.1','-o',build/'active_lab'])
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
    receipt={'tools':tools,'driver_hashes':drivers,'validation_manifests':layers,'platform':platform.platform(),'tests_revision':run('tests-head',['git','rev-parse','HEAD','HEAD^{tree}']),'tests_status':run('tests-status',['git','status','--porcelain']),'binary_sha256':sha(build/'active_lab'),'generated_helper_hashes':{p.name:sha(p) for p in [build/'engine_active.hpp',build/'active_lab_reused.hpp']}}
    if os.environ.get('VULKAN_SKILL_ROOT'):receipt['skill_revision']=run('skill-head',['git','-C',os.environ['VULKAN_SKILL_ROOT'],'rev-parse','HEAD','HEAD^{tree}'])
    (out/'local-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for mode in ['normal','bad-mask','bad-depth']:
        log=run(mode,[build/'active_lab',build/'shaders',out/mode,mode])
        if 'validation_enabled=1' not in log:raise ValueError('validation required')
    result=verify(out/'normal')
    changed=struct.unpack('<3185f',(out/'bad-depth/depth.f32').read_bytes())
    if any(v!=0. for v in changed):raise ValueError('negative depth did not write fragment depth zero')
    changed=struct.unpack('<12740f',(out/'bad-mask/id.f32').read_bytes())
    if any(v!=(4,3,2,1)[i%4] for i,v in enumerate(changed)):raise ValueError('negative active ID output missing')
    for mode,reason in [('bad-mask','active MRT'),('bad-depth','depth')]:
        try:verify(out/mode)
        except ValueError as e:
            if reason not in str(e):raise
        else:raise ValueError('negative not detected')
    summary={'status':'PASS','validation_enabled':True,'active_color_attachments':3,'depth_format':'D32_SFLOAT','numeric':result,'negative_checks':['legal active MRT write mask corruption rejected','legal depth-write corruption rejected'],'scope':'single pass software Vulkan independentBlend write masking and depth write disable; not platform rendergraph integration'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'source-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in [HERE/'main.cpp',HERE/'run_lab.py',HERE/'active.frag',base/'main.cpp',engine]},indent=2)+'\n');print(json.dumps(summary));return 0
if __name__=='__main__':raise SystemExit(main())
