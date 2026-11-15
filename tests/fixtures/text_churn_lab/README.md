# Fixed-resource, 64-generation transfer retirement stress

Actual Vulkan 1.2 timeline-semaphore fixture. Reuses unchanged inflight Lab
setup but keeps its own three command buffers recorded without ONE_TIME_SUBMIT
and three reusable fences. One image, five inherited mapped buffers (one staging
and two readbacks used; two setup buffers unused), three timelines and one pool
remain fixed across 64 generations. No command/buffer/image allocation occurs
inside the generation loop. Only completed fences are reset/reused.

For generation g all three submissions are pending before the host opens the
first gate. Completion counters must be 2g before A, 2g+1 after A with B still
blocked, and 2g+2 after B. The slot cannot be reused at either earlier boundary.
After both consumers and submission fences complete, the next host pattern is
written to the same staging slot. The recorded image upload uses UNDEFINED to
discard old content only after retirement. Two independent readbacks per
generation must exactly match (g+1)/4 + (pixel_index mod 17)/1024. These values
are exactly representable, so the tolerance is zero.

CPU oracle independently checks 128 raw readbacks, every generation counter,
reuse decision and fixture resource inventory. Negative tests reject an older
generation substituted into generation 63 and forged early reuse at generation
31. The real GPU run also injects an exception while generation 31 has pending
submissions: cleanup releases the appropriate final gate, waits tracked fences
with a 10-second bound and destroys resources. Failure to finish exits rather
than destroying in-use objects or calling unbounded device-idle. Process-level
runner and pytest limits are 120 and 180 seconds. Initialization/device-loss/
allocation-failure exhaustive fault injection is not covered; inherited setup
construction does not provide full partial-construction RAII.

Successful cleanup is observed via the post-destructor marker and no validation
diagnostics. Fixed owned-handle inventories and explicit destructor calls are
NOT proof of driver allocator leak freedom, process RSS stability or a production
engine allocator. The retained capacity is reused, not returned to the driver
between generations. There is no descriptor sampling, rendering consumer,
packing/growth/eviction/cancellation policy, multi-device ownership, real
multi-engine integration, multiple-queue hardware
parallelism, mobile certification or performance claim.

```
python tests/fixtures/text_churn_lab/run_lab.py --out /new/output
VULKAN_TEXT18_CHURN=1 python -m pytest -c tests/pytest.ini tests/test_text18_churn_lab.py
```

Provide the explicit official Vulkan SDK prefix, loader, validation-layer path
and ICD environment used by text_inflight_lab. No dependency downloads occur.
Validation must be enabled for this new fixture to pass its independent oracle.
Original two-generation gates are unchanged. Raw logs/provenance/readbacks stay
local; publish only the minimal numerical summary, never environment archives.
