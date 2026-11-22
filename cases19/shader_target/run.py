"""Actual offline GLSL -> SPIR-V target/capability experiments, not device execution."""
import argparse
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import uuid


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tools', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    tools = {name: a.tools / name for name in ('glslangValidator', 'spirv-val', 'spirv-dis')}
    report = {'run_id': str(uuid.uuid4()), 'runner_sha256': sha(pathlib.Path(__file__).read_bytes()),
              'tools': {}, 'cases': {}, 'scope': 'Offline real compiler/validator/disassembler only; no device creation, shader dispatch, enabled feature or hardware support claim.'}
    for name, tool in tools.items():
        r = subprocess.run([str(tool), '--version'], capture_output=True, timeout=30)
        (a.output / (name + '.version.stdout')).write_bytes(r.stdout)
        (a.output / (name + '.version.stderr')).write_bytes(r.stderr)
        if r.returncode or not r.stdout.strip():
            raise RuntimeError('tool version query failed: ' + name)
        report['tools'][name] = {'binary_sha256': sha(tool.read_bytes()), 'version': r.stdout.decode().strip(),
                                'version_stdout_sha256': sha(r.stdout), 'version_stderr_sha256': sha(r.stderr)}

    def invoke(label, tool, args):
        r = subprocess.run([str(tools[tool]), *map(str, args)], capture_output=True, timeout=30)
        (a.output / (label + '.stdout')).write_bytes(r.stdout)
        (a.output / (label + '.stderr')).write_bytes(r.stderr)
        return r, {'exit_code': r.returncode, 'stdout_sha256': sha(r.stdout), 'stderr_sha256': sha(r.stderr)}

    for name, filename, target, version in (
            ('base11', 'base.comp', 'vulkan1.1', 0x10300),
            ('float64_11', 'float64.comp', 'vulkan1.1', 0x10300),
            ('base12', 'base.comp', 'vulkan1.2', 0x10500)):
        source = pathlib.Path(__file__).with_name(filename)
        binary = a.output / (name + '.spv')
        r, compile_log = invoke(name + '.compile', 'glslangValidator', ['-V', '--target-env', target, '-S', 'comp', '-o', binary, source])
        if r.returncode or not binary.exists():
            raise RuntimeError(name + ': compilation failed')
        data = binary.read_bytes()
        if len(data) < 20 or len(data) % 4 or struct.unpack_from('<I', data)[0] != 0x07230203 or struct.unpack_from('<I', data, 4)[0] != version:
            raise ValueError('unexpected SPIR-V header/version')
        r, validation = invoke(name + '.validate', 'spirv-val', ['--target-env', target, binary])
        if r.returncode or r.stdout or r.stderr:
            raise RuntimeError(name + ': matching target validation failed')
        validation.update(artifact_sha256=sha(data), target_env=target)
        dis_path = a.output / (name + '.spvasm')
        r, dis_log = invoke(name + '.disassemble', 'spirv-dis', [binary, '-o', dis_path])
        if r.returncode or not dis_path.exists():
            raise RuntimeError('disassembly failed')
        dis = dis_path.read_text()
        capabilities = re.findall(r'^\s*OpCapability\s+(\w+)\s*$', dis, re.M)
        extensions = re.findall(r'^\s*OpExtension\s+"([^"]+)"\s*$', dis, re.M)
        if extensions != []:
            raise ValueError('unexpected SPIR-V extensions: ' + repr(extensions))
        expected = ['Shader', 'Float64'] if name == 'float64_11' else ['Shader']
        if sorted(capabilities) != sorted(expected):
            raise ValueError('unexpected capabilities: ' + repr(capabilities))
        if name == 'float64_11' and not re.search(r'OpTypeFloat\s+64\b', dis):
            raise ValueError('Float64 capability without real float64 type')
        case = {'source': filename, 'source_sha256': sha(source.read_bytes()), 'target_env': target,
                'spirv_header_version': hex(version), 'spirv_sha256': sha(data),
                'disassembly_sha256': sha(dis_path.read_bytes()), 'capabilities': capabilities, 'extensions': extensions,
                'extraction': {'artifact_sha256': sha(data), 'exit_code': dis_log['exit_code'], 'capabilities': capabilities, 'extensions': extensions, 'disassembly_sha256': sha(dis_path.read_bytes())},
                'compile': compile_log, 'validate': validation, 'disassemble': dis_log,
                'status': 'OFFLINE_TOOL_PAIR_PASS'}
        if name == 'base12':
            r, mismatch = invoke(name + '.mismatch11', 'spirv-val', ['--target-env', 'vulkan1.1', binary])
            message = r.stderr.decode()
            if r.returncode <= 0 or 'Invalid SPIR-V binary version 1.5 for target environment SPIR-V 1.3 (under Vulkan 1.1 semantics)' not in message:
                raise ValueError('wrong-target failure was missing or unrelated')
            case['wrong_target'] = {'artifact_sha256': sha(data), 'target_env': 'vulkan1.1', 'status': 'EXPECTED_VERSION_REJECTION', **mismatch,
                                    'diagnostic': message.strip()}
        report['cases'][name] = case
    report['status'] = 'OFFLINE_TARGET_CAPABILITY_PAIR_PASS'
    report['limitations'] = ['Float64 capability requires separate device shaderFloat64 support query and enablement; neither is tested.',
                             'Validator acceptance does not establish runtime correctness, device support, feature enablement or rendering quality.',
                             'Target mismatch negative is validator version enforcement, not a Vulkan driver diagnostic.']
    (a.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])


if __name__ == '__main__':
    main()
