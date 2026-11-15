# Local software Vulkan MSDF cost diagnostic

Fresh preparation validates the unchanged baseline and binary16/linear4 variants.
The same 65×49 A-native atlas, render targets and validation configuration are
used for all three modes. Five warmup cycles precede 30 measured cycles. The
first mode rotates each cycle; modes never execute concurrently. Raw samples and
nearest-rank p50/p95/max are retained. No relative-speed assertion is made.

A dedicated command buffer contains query reset, TOP_OF_PIPE timestamp, one
render pass, and BOTTOM_OF_PIPE timestamp. Upload/clear is separately submitted
and waited before this buffer; readback is separately submitted afterward.
Thus compilation, device creation, upload, readback and process startup are
excluded from the GPU timestamp interval. Render pass/load/store/raster work
remains included: this is not pure fragment shader time. CPU vkQueueSubmit and
fence-wait times are separate steady-clock measurements; query reads occur after
both and are not included. CPU wait overlaps GPU execution, so do not add GPU and
CPU wait costs. Validation overhead remains and small offscreen workloads are
not reliable extrapolations to applications.

The actual queue's timestampValidBits, timestampPeriod and
 timestampComputeAndGraphics are checked; pool creation failure or unavailable
capability reports NOT_MEASURED. Query availability is checked after a fence;
64-bit values are masked to valid bits before conversion. The device is the
configured software Vulkan implementation, not a mobile GPU. No mobile frame
budget, sustained performance, power or thermal claim is supported.

Run with the existing trusted preparation environment:
```
python tests/fixtures/text_msdf_cost_lab/run_lab.py --out NEW_DIRECTORY \
  --font APPROVED_DEJAVU_SANS --msdf-source PINNED_MSDFGEN
```
Opt-in: VULKAN_TEXT18_MSDF_COST=1 and TEXT18_MSDF_SOURCE set. Existing baseline
font and source guards remain in force; no third-party source is redistributed.

Outside the timed interval every warmup/measured draw's entire RGBA readback is
compared with its freshly validated preparation result (absolute 2e-6 tolerance),
and velocity/ID sentinels are compared exactly. A skipped or incorrect draw
therefore cannot qualify merely by producing a short timing and finite pixels.
This fixture requires an actual CPU-type Vulkan device; others report
NOT_MEASURED. Limited-bit timestamp intervals also reject possible multiple wraps
when the enclosing CPU submit+wait interval reaches the counter wrap period.
