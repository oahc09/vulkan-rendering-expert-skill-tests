import os,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
def build(source,b,near,mirror,wrongshadow,run):
 shutil.copytree(source,b)
 v=(HERE/'world.vert').read_text();f=(HERE/'world.frag').read_text();assert f.count('// PANEL')==1;f=f.replace('// PANEL',(HERE.parent/'scene_b_vector_overlay_lab/panel.glsl').read_text())
 light=(HERE.parent/'text_shadow_lab/shadow.vert').read_text();assert light.count('p.xy+vec2(.5,.25)*p.z')==1
 if mirror and not wrongshadow:light=light.replace('p.xy+vec2(.5,.25)*p.z','vec2(65-p.x,p.y)+vec2(.5,.25)*p.z')
 for name,text in [('fullscreen.vert',v),('coverage.frag',f),('shadow.vert',light)]:
  file=b/name;file.write_text(text);run('compile-'+b.name+'-'+name,[os.environ['GLSLANG'],'-V','--target-env','vulkan1.2','-DNEAR='+str(near),'-DMIRROR='+str(int(mirror)),file,'-o',b/'shaders'/(name+'.spv')]);run('validate-'+b.name+'-'+name,[os.environ['SPIRV_VAL'],'--target-env','vulkan1.2',b/'shaders'/(name+'.spv')])
 # Prior combined C++ does not embed shader source: identical binary, immutable
 # source vertex geometry, distinct actual shader variants loaded at creation.
 return b
