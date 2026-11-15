import os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
COMMIT='1874bcf7d9624ccc85b4bc9a85d78116f690f35b'
def build(out,source,run):
 source=Path(source)
 if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=30).strip()!=COMMIT:raise ValueError('unpinned generator')
 if subprocess.check_output(['git','-C',str(source),'status','--porcelain','--untracked-files=all'],text=True,timeout=30).strip():raise ValueError('dirty generator')
 flags=subprocess.check_output(['git','-C',str(source),'ls-files','-v','-z'],timeout=30).split(b'\0')
 if any(r and (r[:1].islower() or r[:1]==b'S') for r in flags):raise ValueError('hidden dependency index flags')
 for p in [source/'msdfgen.h',source/'LICENSE.txt',*sorted((source/'core').glob('*'))]:
  if p.is_file() and (p.is_symlink() or p.read_bytes()!=subprocess.check_output(['git','-C',str(source),'show',COMMIT+':'+str(p.relative_to(source))],timeout=30)):raise ValueError('dependency blob mismatch')
 base=HERE.parent/'text_vector_lab';run('base-build',[base/'build.sh',out])
 run('generator-build',[os.environ.get('CXX','g++'),'-std=c++17','-O2','-DMSDFGEN_PUBLIC=','-DMSDFGEN_USE_CPP11','-I'+str(source),HERE.parent/'text_msdf_lab/generate.cpp',*sorted((source/'core').glob('*.cpp')),'-o',out/'generate'])
 def rep(s,a,b,n=1):
  if s.count(a)!=n:raise ValueError('hook drift: '+a)
  return s.replace(a,b)
 core=(HERE.parent/'engine_scale_lab/main.cpp').read_text();im=core[core.index('  Image image('):core.index('  VkShaderModule shader(')]
 im=rep(im,'Image image(','Image boardImage(');im=rep(im,'{width, height, 1}','{width, height*16, 1}')
 im=rep(im,'    Image im;','    if(props.maxExtent.width<width||props.maxExtent.height<height*16)throw std::runtime_error("texture extent unsupported");\n    Image im;')
 cpp=(base/'main.cpp').read_text();cpp=rep(cpp,'int main(int argc,char** argv)','int old_board_main(int argc,char** argv)');cpp=rep(cpp,'../engine_scale_lab/main.cpp',str(HERE.parent/'engine_scale_lab/main.cpp'))
 cpp=rep(cpp,'struct TextLab: Vulkan {','struct TextLab: Vulkan {\n float transform=0,mode=0,layers=1,colored=0;\n'+im)
 cpp=rep(cpp,'VK_FORMAT_R32_SFLOAT','VK_FORMAT_R32G32B32A32_SFLOAT',2)
 cpp=rep(cpp,'coverage=image(','coverage=boardImage(')
 cpp=rep(cpp,'buffer(width*height*4,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)','buffer(width*height*16*16,VK_BUFFER_USAGE_TRANSFER_SRC_BIT)')
 cpp=rep(cpp,'VK_SHADER_STAGE_FRAGMENT_BIT,0,16','VK_SHADER_STAGE_FRAGMENT_BIT,0,32',2)
 cpp=rep(cpp,'mask.size()!=width*height','mask.size()!=width*height*4*16')
 cpp=rep(cpp,'copy.imageExtent={width,height,1}','copy.imageExtent={width,height*16,1}')
 cpp=rep(cpp,'float rgba[]={ink[0],ink[1],ink[2],ink[3]};','float rgba[]={ink[0],ink[1],ink[2],ink[3],transform,mode,layers,colored};')
 (out/'board.hpp').write_text(cpp)
 args=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(out)]
 if os.environ.get('VULKAN_SDK_PREFIX'):args+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('board-build',args+[HERE/'main.cpp','-l:libvulkan.so.1','-o',out/'board'])
 for name,define in [('correct',None),('double-alpha','DOUBLE_ALPHA'),('wrong-range','WRONG_RANGE')]:
  folder=out/name;folder.mkdir()
  for p in (out/'shaders').glob('*.spv'):(folder/p.name).write_bytes(p.read_bytes())
  args=[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2']
  if define:args+=['-D'+define+'=1']
  run('shader-'+name,args+[HERE/'board.frag','-o',folder/'coverage.frag.spv']);run('validate-'+name,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',folder/'coverage.frag.spv'])
