# RGBA8 combined-image-sampler 场景

Real Vulkan 1.1 CPU ICD: upload a non-symmetric 4×4 RGBA8_UNORM endpoint-color
texture, normalized nearest/clamp sampler at explicit LOD 0, compute sample to
rgba8 storage image, copy and fence-retired coherent full 16-pixel readback.
The independently computed CPU reference uses floor/clamp texel selection and
channel tuples, not the C success boolean. All channels are exactly 0/255;
this avoids claiming general floating-point UNORM rounding equivalence.

UV=(pixel+(-0.5,1.5))/4 intentionally exercises **negative u and high v** edge
clamping plus texel centers. Right and low-v edge tests, linear interpolation,
sRGB, mip chains, anisotropy, compare samplers, arrays and hardware performance
are not included. The sampled result differs under transpose and axis reversal.
Both images actually use the same queried union usage: SAMPLED|STORAGE|TRANSFER
SRC|DST. This is not a claim that each image uses a minimal separate usage query.

```
export VK_DRIVER_FILES=/path/to/lvp_icd.json
export VK_LAYER_PATH=/path/to/explicit_layer.d
export LD_LIBRARY_PATH=/path/to/tool-libraries
export MESA_SHADER_CACHE_DISABLE=true
python -O cases19/texture_sampling/run.py \
 --tools /path/to/glslang-and-spirv-tools --include /path/to/include \
 --loader /path/to/libvulkan.so.1 --validusage /path/to/validusage.json \
 --output FRESH_DIRECTORY
```

Requires exact pinned validusage 1.4.309 and matching actual Validation layer,
software CPU device, required format/descriptor/compute limits and compatible
host-coherent memory. Missing capability or timeout does not produce PASS.
Compile/validation/disassembly, tools/source/binary and raw outputs are hashed.
Bounded SPIR-V checks are not general shader reflection. Synchronization
Validation's shader-access heuristic is enabled; clean output is not proof of
all possible synchronization behavior.

Three modes: normal succeeds with all expected pixels; bad-sampler creates a
sampler with unnormalized coordinates and LINEAR mipmapMode, violating exact
`VUID-VkSamplerCreateInfo-unnormalizedCoordinates-01073`. Other unnormalized
constraints remain legal; Validation callback aborts creation, the undefined
failed handle is cleared, no descriptor or submission uses it. Wrong-output
flips one expected output bit and must really return 6. Negative callback exit 0
means expected rejection, not successful Vulkan creation. Zero output in the
unsubmitted mode is a placeholder, not rendered pixels.

Objects remain alive through fence completion. Failed device-idle cleanup exits
nonzero without destroying possibly pending resources; this boundary is source
reviewed, not a driver-hang recovery experiment. These are authored controlled
fixtures, not external production defects, repair patches or full domain/release
acceptance. The first runner attempt was blocked by a manifest string/int
comparison; that failed run is retained separately, not counted as passed.
