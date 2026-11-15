import importlib.util,os
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(out,source,run):
 p=HERE.parent/'scene_a_refined_board_lab/build.py';spec=importlib.util.spec_from_file_location('full_build',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.build(out,source,run)
 s=(out/'board.hpp').read_text()
 for old,new,n in [('{260, 3136, 1}','{packedWidth, packedHeight, 1}',1),('props.maxExtent.width<260||props.maxExtent.height<3136','props.maxExtent.width<packedWidth||props.maxExtent.height<packedHeight',1),('buffer(65*49*16*256,','buffer(packedWidth*packedHeight*16,',1),('mask.size()!=65*49*64*16','mask.size()!=packedWidth*packedHeight*4',1),('copy.imageExtent={260,3136,1}','copy.imageExtent={packedWidth,packedHeight,1}',1),('VK_SHADER_STAGE_FRAGMENT_BIT,0,48','VK_SHADER_STAGE_FRAGMENT_BIT|VK_SHADER_STAGE_VERTEX_BIT,0,48',2),('vkCmdDraw(cb,3,1,0,0)','vkCmdDraw(cb,6,1,0,0)',1)]:
  if s.count(old)!=n:raise ValueError('helper hook drift '+old)
  s=s.replace(old,new)
 (out/'board.hpp').write_text(s)
 cpp=(HERE.parent/'scene_a_refined_board_lab/main.cpp').read_text()
 for token in ['#include "board.hpp"','argc!=4','tr>5','std::filesystem::path root=argv[3];','65*49*16*256','65*49*64*16']:
  if cpp.count(token)!=1:raise ValueError('main hook drift '+token)
 cpp=cpp.replace('#include "board.hpp"','static unsigned packedWidth=0,packedHeight=0;\n#include "board.hpp"').replace('argc!=4','argc!=6').replace('tr>5','tr>6').replace('std::filesystem::path root=argv[3];','packedWidth=std::stoul(argv[4]);packedHeight=std::stoul(argv[5]);if(packedWidth<3||packedWidth>1024||packedHeight<2||packedHeight>2048)throw std::runtime_error("packed extent budget");\n std::filesystem::path root=argv[3];').replace('65*49*16*256','packedWidth*packedHeight*16').replace('65*49*64*16','packedWidth*packedHeight*4')
 (out/'compact.cpp').write_text(cpp)
 args=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-I'+str(out)]
 if os.environ.get('VULKAN_SDK_PREFIX'):args+=['-I'+os.environ['VULKAN_SDK_PREFIX']+'/include']
 run('compact-build',args+[out/'compact.cpp','-l:libvulkan.so.1','-o',out/'compact_lab'])
 for variant,define in [('compact',None),('wrong-metadata','WRONG_METADATA'),('wrong-inverse','WRONG_INVERSE')]:
  folder=out/variant;folder.mkdir()
  for p in (out/'correct').glob('*.spv'):(folder/p.name).write_bytes(p.read_bytes())
  args=[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2']
  if define:args+=['-D'+define+'=1']
  run('vertex-'+variant,[os.environ.get('GLSLANG','glslangValidator'),'-V','--target-env','vulkan1.2',HERE/'perspective.vert','-o',folder/'fullscreen.vert.spv']);run('vertex-val-'+variant,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',folder/'fullscreen.vert.spv'])
  run('shader-'+variant,args+[HERE/'compact.frag','-o',folder/'coverage.frag.spv']);run('spirv-'+variant,[os.environ.get('SPIRV_VAL','spirv-val'),'--target-env','vulkan1.2',folder/'coverage.frag.spv'])
