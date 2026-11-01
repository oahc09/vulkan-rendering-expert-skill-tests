#!/usr/bin/env python3
"""Check actual compiled SPIR-V ABI; not a complete engine reflection/schema verifier."""
import hashlib,json,os,pathlib,re,subprocess,sys
root=pathlib.Path(__file__).parent
build=pathlib.Path(sys.argv[1])
dis=os.environ.get('SPIRV_DIS','spirv-dis')
code=subprocess.check_output([dis,str(build/'shaders/cull.comp.spv')],text=True)
for member in range(12):
    assert re.search(rf'OpMemberDecorate %Push {member} Offset {member*4}\b',code)
for member,offset in [(0,0),(1,16)]:
    assert re.search(rf'OpMemberDecorate %Object(?:_\d+)? {member} Offset {offset}\b',code)
assert re.search(r'OpDecorate %_runtimearr_Object(?:_\d+)? ArrayStride 32\b',code)
assert re.search(r'OpDecorate %_runtimearr_Draw(?:_\d+)? ArrayStride 16\b',code)
# Test the checker rejects a concrete ABI mutant rather than only testing happy regexes.
mutant=code.replace('ArrayStride 32','ArrayStride 28')
assert not re.search(r'OpDecorate %_runtimearr_Object(?:_\d+)? ArrayStride 32\b',mutant)
manifest={'layer':'ShaderUnit','status':'PASS','target_vulkan':'vulkan1.2','target_spirv':'1.5',
 'compiler':subprocess.check_output([os.environ.get('GLSLANG','glslangValidator'),'--version'],text=True),
 'compiler_options':['-V','--target-env','vulkan1.2','-Ishaders'],
 'includeDependencyHashes':{'common.glsl':hashlib.sha256((root/'shaders/common.glsl').read_bytes()).hexdigest()},
 'shaders':[],'interfaceContract':'Object std430 offsets0/16 stride32; Push offsets0..44; Draw stride16',
 'limitations':'No full descriptor-schema/stage-interface reflection or device compatibility certification'}
for path in sorted((build/'shaders').glob('*.spv')):
    source=root/'shaders'/path.name.removesuffix('.spv')
    manifest['shaders'].append({'source':source.name,'sourceHash':hashlib.sha256(source.read_bytes()).hexdigest(),
      'bytecodeHash':hashlib.sha256(path.read_bytes()).hexdigest(),'entryPoint':'main','stage':source.suffix[1:]})
print(json.dumps(manifest,indent=2))
