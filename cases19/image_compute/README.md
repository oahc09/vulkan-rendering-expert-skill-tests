# Integrated image upload → compute → readback repair

An original controlled integration experiment, **not an external production bug**.
It crosses image allocation/layout, descriptor/pipeline, shader execution,
synchronization and host completion in one executable and one pixel oracle.

## Positive chain

1. Query R32_UINT, 2D, optimal tiling, actual union usage
   `TRANSFER_SRC | TRANSFER_DST | STORAGE` (11), flags 0, and require sample 1,
   adequate extent and storage-image limits. Both images use this same union;
   this is not a claim of two separate minimal-usage queries.
2. Allocate compatible images and separate compatible HOST_VISIBLE | HOST_COHERENT
   upload/readback buffers. Record memoryTypeBits, size, alignment and chosen type.
3. Fill upload buffer with spatially varying uint input `5 + 11*i`, all 16 values.
   Initialize readback to a sentinel, not to expected output.
4. Transition input and output from UNDEFINED to GENERAL. Upload all 4×4 input
   texels using buffer-to-image copy in GENERAL (legal for this command).
5. Issue GENERAL→GENERAL image barrier with transfer-write→compute-shader-read.
   This memory dependency is distinct from changing image layout.
6. Bind two storage-image descriptors with imageLayout GENERAL, compile/validate
   real GLSL, create pipeline and dispatch 4×4 workgroups of size 1. Shader executes
   actual imageLoad and imageStore: `output = input * 3 + 7`.
7. Issue output GENERAL→TRANSFER_SRC_OPTIMAL barrier with compute-write→transfer-read,
   copy image to readback buffer, then transfer-write→host-read buffer barrier.
8. Submit, wait for fence success, read coherent memory and compare **every uint
   exactly**: 22, 55, …, 517. This is a numeric image oracle, not visual SSIM.

No optional shader features are enabled. R32ui is used, not filtered sampling.

## Repair and independent controls

The runner actually applies the readable one-line patch to a copy of baseline.c,
verifies no other text changed and builds both sources with the same real shader.

| Run | Actual result |
| --- | --- |
| baseline with missing upload memory dependency | compute-dispatch SyncVal READ_AFTER_WRITE, callback abort, never submitted |
| patched positive | exact 16-pixel output and zero diagnostics |
| patched missing readback dependency | GENERAL stays legal; image-to-buffer copy reports readback READ_AFTER_WRITE, never submitted |
| patched bad descriptor/current layout agreement | dispatch VUID 00344 and 08114, never submitted |
| patched wrong-output oracle | actual correct pixels, deliberately wrong expectation, exit 6 |
| same baseline with shader-access heuristic disabled | hazard not detected, exit 5, **not a pass** |

Exact diagnostic names and phases are checked. Unexpected errors, crashes,
missing tools/capabilities, cleanup errors and timeouts cannot count as a pass.
Invalid commands are aborted by the validation callback. Negative command buffers
are never submitted; their recording resources are destroyed during cleanup.

## SyncVal detection limitation

The pinned Validation layer's `syncval_shader_accesses_heuristic` defaults false.
The runner explicitly enables its documented manifest setting through
`VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC=true`, and retains a separate actual
OFF run of the same baseline. Shader access analysis is a **static heuristic**:
it can miss accesses or produce false positives. This is not GPU-assisted
validation or a proof that all shader dependencies are covered. The clean patched
run plus independent CPU pixel oracle supplies execution evidence separately.

## Reproduction and evidence

Configure VK_DRIVER_FILES, VK_LAYER_PATH and LD_LIBRARY_PATH for the CPU ICD and
Validation layer, then:

```sh
python -O cases19/image_compute/run.py --tools "$TOOL_BIN" \
  --include "$VULKAN_INCLUDE" --loader "$VULKAN_LOADER" \
  --output "$FRESH_OUTPUT_DIRECTORY"
```

Output must not already exist. Summary records source/patch/runner/tool/executable/
SPIR-V/disassembly/loader/manifest hashes, versions, exact diagnostics and return
codes, input and output pixel arrays, actual format queries, image/buffer allocation
records, descriptor layouts, barrier stages/access masks/layouts/subresources,
copy extents and fence completion. Those records are printed from the C structures
used for real calls, and the runner checks the bounded chain against them. Raw
stdout/stderr and built artifacts remain beside the summary.

Scope: CPU software ICD, one compute queue, coherent staging/readback, R32_UINT,
4×4, one mip/layer/sample. **Noncoherent visibility remains unrun**. No cross-queue,
sparse/alias/multiplanar, filtered texture, mobile performance, hardware certification
or external-project acceptance is claimed.
