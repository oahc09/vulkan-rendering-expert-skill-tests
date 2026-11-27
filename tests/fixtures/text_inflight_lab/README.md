# TEXT18 in-flight image retirement (actual Vulkan)

This deliberately small integration fixture queries and enables Vulkan 1.2
`timelineSemaphore`, then uses one transfer-capable queue and one R32_SFLOAT
image slot. Missing capability is BLOCKED/FAIL, never silently CPU emulated.

All three first-generation submissions are queued before host release:

```
producer:    wait hostGate=1, staging A -> slot, signal ready=1
consumer A:  wait ready=1, slot -> readback A, signal done=1
consumer B:  wait hostGate=2 AND done=1, slot -> readback B, signal done=2
```

The host queries the actual GPU completion timeline, not a CPU frame index:
- before gate 1: done=0; reuse is rejected;
- after gate 1 and waiting done=1: B remains gated, done=1; reuse is rejected;
- after gate 2 and waiting done=2: all first-generation consumers retired;
- only now record/submit staging B -> the same slot, then consumer C readback,
  finishing at done=3. Old A/B readback bytes must still contain generation 0;
  C must contain distinct generation 1.

Each generation has its own staging buffer; each consumer has its own readback.
All operations use legal image layouts, transfer barriers and host visibility.
The early-reuse checks only reject through the guard. No invalid GPU use-after-
free or overwrite is injected. Host timeline gates make the pending boundaries
observable even on a fast software driver, without requiring a second queue.

Readbacks use exactly representable float patterns over 32x24 pixels; tolerance
is exactly zero. The independent Python verifier checks every float, phases,
watermark and reuse decision. Negative verifier tests reject premature-reuse
records and stale-generation readbacks. This is evidence for the mechanism,
not proof of sampled-render/descriptor retirement, real atlas packing/churn,
multiple hardware queues, target devices or performance.

Run in an already authorized environment with official Vulkan headers, loader,
ICD and optional Khronos validation layer:

```
python tests/fixtures/text_inflight_lab/run_lab.py --out /new/output
VULKAN_TEXT18_INFLIGHT=1 python -m pytest -c tests/pytest.ini tests/test_v1_0_18_inflight_lab.py
```

`VULKAN_SDK_PREFIX`, `VK_DRIVER_FILES`, `VK_LAYER_PATH`, `LD_LIBRARY_PATH`, and
`CXX` are supported. The fixture never downloads anything. Raw source, compiler,
driver and artifact hashes plus device properties and validation log are saved
locally. Existing output is refused. The opt-in test is SKIP without explicit
enablement; absent validation layer is reported, not described as validation
success. There is no font or third-party test asset and no ZIP creation/upload.

All timeline waits and cleanup fence waits use a 10-second limit; the Python
runner bounds each subprocess at 120 seconds. Error cleanup releases host gate 2
before waiting on submitted fences. A cleanup timeout exits the process as an
explicit failure rather than destroying resources still in use. A deliberate
abort after all three pending submissions verifies this cleanup path and must
exit with the expected error, without validation diagnostics or a timeout.
