# Direct host-visible input vs staging upload: actual A/B/A

Run the fixed one-shot scene:

```sh
python cases19/upload_choice/run.py \
 --tools /official-tools/bin --include /official-headers/include \
 --loader /official-loader/libvulkan.so.1 \
 --icd /selected/icd.json --libdir /selected/libraries \
 --layerdir /official-validation/manifests \
 --spec-root /frozen-Vulkan-Docs-368 --requested-budget 512 \
 --output /fresh/output
```

All arguments select local trusted tools/data, not arbitrary project commands.
The exact supplied ICD must enumerate one CPU device. Each run creates a fresh
logical device and a single compute queue. Fixed order is direct→staging→direct,
followed by wrong-reference controls for each path. No old result is imported.

The CPU writes 64 values `7*i+3`; the same validated SPIR-V computes `3*input+i`.
Direct uses a coherent host-visible STORAGE buffer. Staging uses a coherent host
TRANSFER_SRC buffer and an actual copy into a DEVICE_LOCAL STORAGE|TRANSFER_DST
buffer. The latter is deliberately not mapped even if the actual type permits it.
Each path has its own coherent output buffer, read only after its fence completes.
All 64 raw input and output words are checked independently by Python. The second
direct receipt must exactly equal the first (except observed execution interval,
which is not part of the verified allocation/output receipt).

HOST_WRITE→TRANSFER_READ/SHADER_READ barriers are conservative, not asserted
mandatory for writes already made available before queue submission. Staging's
TRANSFER_WRITE→COMPUTE_SHADER/SHADER_READ and output's SHADER_WRITE→HOST_READ
are actual range-specific dependencies. Coherence removes flush/invalidate here,
not completion, ordering or lifetime requirements. All resources stay live through
fence completion. A failed completion attempts device retirement; if that fails,
the process fails without unsafe destruction. This is source-audited failure
handling, not an injected device-loss/recovery test.

The supplied frozen memory/resources/synchronization sources are hash checked and
raw anchor slices recorded. Conditional/include dependencies are not expanded.
The ordinary VVL 1.4.309 errors are collected; these positive paths and wrong
CPU references must have zero error callbacks. Wrong-reference exit6 is an oracle
control, not an API misuse or synchronization-negative test. No unsafe command
or undefined memory access is submitted.

## What the budget means

Every actual allocation request includes logical bytes, VkMemoryRequirements
size/alignment/typeBits, chosen type flags and heap index/size/flags, actual usage,
binding offset and mapping policy. All allocations coexist at execution, so their
sum is an observed simultaneous requested-allocation amount, **not** residency,
heap usage, physical VRAM peak or driver overhead.

On this llvmpipe cohort both paths use the same flags15 memory type. Direct
requests512 bytes; staging768 bytes including its extra upload buffer. This is
not evidence of physically separate host/device memory domains or discrete-GPU
performance. Policy retains the verified direct baseline whenever its request
fits; if neither fits it rejects both. It does not generically optimize memory
architecture. `--require-performance` returns NEEDS_MEASUREMENT even when budgets
fit. CPU submit-to-fence-wait duration is an observation under Validation, not GPU
timing, a full-frame measure or a controlled speed comparison.

The new path integrates transfer, descriptor, dispatch and retirement in one
same-input comparison; it does not claim noncoherent upload, multi-queue overlap,
streaming/sparse residency, frame-time, mobile thermal or whole C2 completion.
