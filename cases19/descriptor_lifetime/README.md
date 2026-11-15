# Ordinary descriptor lifetime: real API joint experiment

Original deliberate fault injection, not an external production defect. One
CPU-ICD, single-queue compute path. The runner builds GLSL UBO to SSBO, validates
SPIR-V and queries/enables timeline semaphore support on Vulkan 1.2.

The first dispatch waits for unsignaled timeline value 1; its fence must be
VK_NOT_READY. In bad mode, an ordinary pending descriptor update must produce
exactly VUID-vkUpdateDescriptorSets-None-03047 in the pending-update phase. The
callback aborts that invalid update. Host signal releases the submission and
readback must equal 42. After completion, a legal update selects a second UBO;
the invalidated command buffer is reset and re-recorded before dispatch. The
second readback must equal 99. Good mode omits the pending update and has no
errors. Wrong-output mode deliberately expects 100 and must exit 6, not pass.

Configure VK_DRIVER_FILES and VK_LAYER_PATH for a software ICD and validation
layer. Invoke run.py with --include, --loader, --glslang, --spirv-val,
--layer-manifest and a new --output directory. No tools are downloaded by it.
Actual binaries, sources, SPIR-V, tool versions and runtime identity are recorded.
Unsupported scope, timeout, errors or mismatches fail, including under python -O.
The subprocess deadline bounds any failure-path cleanup hang as a non-PASS.

Raw logs/build paths remain local; review summaries before publishing. No claim
of hardware support, performance, general shader correctness, update-after-bind,
indexing, SC execution, external-project repair or Live-model acceptance.

Only ordinary Validation is enabled here, not SyncVal or GPU-AV. The wrong-output
case is an authored oracle negative control, not independent defect discovery.
