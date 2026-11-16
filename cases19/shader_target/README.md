# Offline shader target and capability pair

Real GLSL is compiled by glslangValidator, validated by spirv-val and disassembled
by spirv-dis. No hand-authored SPIR-V or fabricated compiler output is used.

| Source | Compiler target | Binary version | Validator target | Expected |
| --- | --- | --- | --- | --- |
| base.comp | Vulkan 1.1 | SPIR-V 1.3 | Vulkan 1.1 | accepted, Shader |
| float64.comp | Vulkan 1.1 | SPIR-V 1.3 | Vulkan 1.1 | accepted, Shader + Float64 |
| base.comp | Vulkan 1.2 | SPIR-V 1.5 | Vulkan 1.2 | accepted, Shader |
| same base12 binary | unchanged | SPIR-V 1.5 | Vulkan 1.1 | rejected for version mismatch |

The Float64 source writes a real double-precision storage-buffer member. The runner
requires both `OpCapability Float64` and `OpTypeFloat 64` in real disassembly.
The mismatch negative must exit nonzero with the specific version diagnostic;
a missing tool, crash, timeout or unrelated error is not counted as that negative.
All three successful validator invocations must exit zero without diagnostics.

Run with the supplied official compiler/SPIRV-Tools installation:

```sh
python -O cases19/shader_target/run.py --tools "$TOOL_BIN" --output "$FRESH_OUTPUT"
```

A new output directory is mandatory. It records tool version outputs and binary
hashes, GLSL source/runner hashes, each SPIR-V binary's header version/hash,
disassembly/hash, compiler and validator targets, return codes and stdout/stderr
hashes. Raw logs and binaries remain alongside `summary.json`. Build flags are
`-V --target-env <target> -S comp -o <output> <source>`; validation uses
`--target-env <target> <binary>`; disassembly uses `<binary> -o <assembly>`.
Reported version strings are actual executable output, not inferred package labels.

## Strict limits

This is an offline tool-pair check and deliberate target mismatch, not a driver
experiment or external production bug. Validator success does **not** prove device
feature support, enabled features, dispatch correctness or visual quality.
`Float64` requires a separately queried and enabled `shaderFloat64` device feature;
no Vulkan device is created here. No mobile hardware qualification is claimed.
