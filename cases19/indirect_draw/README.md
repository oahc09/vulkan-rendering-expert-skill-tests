# GPU-generated ordinary indirect draw
Original repository-authored bounded CPU ICD experiment, not an external production bug. Standalone cohort, not silently added to older five-chain bundle.
```
python -O cases19/indirect_draw/run.py --tools OFFICIAL_TOOLS --include HEADERS --loader LOADER --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```
A32-byte compatible coherent STORAGE|INDIRECT buffer is initialized to zero, not prefilled with correct commands. A real compute shader writes VkDrawIndirectCommand [3,1,0,0]. Explicit COMPUTE_SHADER/SHADER_WRITE→DRAW_INDIRECT/INDIRECT_COMMAND_READ memory barrier precedes vkCmdDrawIndirect(count1). Real vertex+fragment pipeline outputs a4×4 nonconstant red/blue checker; CPU independently checks every pixel after color→transfer copy, host dependency and fence. Separate compute→host dependency allows readback of actual generated four words, checked in addition to pixels.

Runtime records core dynamicRendering support/enable, graphics/compute-capable queue, supported multiDrawIndirect/drawIndirectFirstInstance and limit maxDrawIndirectCount. Neither optional feature is enabled in VkDeviceCreateInfo; one draw and firstInstance0 need neither. Graphics/attachment policies are jointly reused and all helper hashes recorded. Real three-stage GLSL→SPIRV compilation, validation, disassembly and tools/version/hash provenance retained.

Negative offset2 retains bufferSize32 so18 bytes fit, isolating VUID-vkCmdDrawIndirect-offset-02710. Validation callback aborts the void draw, entire command buffer is reset/discarded, never submitted. No invented VkResult. Wrong-output compares inverted checker CPU expectation and must exit6. No missing-barrier/SyncVal shader heuristic experiment claimed.

Policy distinguishes count0 (no range consumption), count1 (stride ignored), and count>1 (stride/range/multiDraw requirements). Actual path only count1; CPU synthetic count0/multiDraw cases are not device proof. Generated firstInstance must be known, nonzero requires enabled feature; generated content is not validated by ordinary VVL alone. Timestamp/performance/hardware/mobile, indexed/count-buffer variants, multiqueue, all VK11 and full-domain acceptance remain unverified. Checker symmetry cannot detect transpose. CPU ICD still executes real Vulkan compute, not a physical GPU timing claim.

Actual no-dispatch causal control keeps initialized zeros, produces zero generated args and only magenta clear pixels, exiting4; this distinguishes real compute-produced indirect work from a CPU-prefilled command or clear-only success. Actual graphics+compute queue bits and compute limits are recorded. CPU policy rejects uint32/uint64 overflow before range interpretation.
