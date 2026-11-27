# Actual upload admission, backpressure and independent epoch accounting

This bounded experiment implements the original plan's observable upload/task
budget on top of the existing real pending packed-glyph consumer. Capacity is
one 65x49 R32F payload (12,740 bytes) per declared epoch and one in-flight upload
at a time. These are explicit fixture inputs, not product throughput thresholds,
Vulkan allocation sizes, VRAM limits or CPU font-service cache budgets.

All deliberate dimension, overflow, mask and budget checks occur before Engine
page creation, staging allocation or command recording. Six invalid inputs
(nonfinite/negative dimensions, byte multiplication overflow, unsupported extent,
short mask, nonfinite mask) reject with exact reasons. Rejection records include
before/after epoch charge, in-flight charge/tasks, accepted count, page/submission
objects, live staging handles/payload and actual published generation. No deliberate
rejection may change any of these fields.

Three cycles each submit an old-page draw behind a real timeline gate, then enqueue
one candidate upload behind it. Both fences are checked NOT_READY. A second request
is rejected by the epoch byte budget. Canceling the candidate prevents publication
but does not cancel its GPU work or release its task/payload capacity. Early
completion is rejected by the actual unsignaled upload fence. Advancing the epoch
resets only the epoch charge: another request still fails the in-flight limit.
After signaling and waiting for both actual submissions, the old image is read
back; the canceled upload and old draw resources are actually destroyed, freed
and erased, and the canceled page retires. A retry in the new epoch uploads and
publishes a replacement, draws it, and retires the old page. The following request
still fails the epoch budget even though no upload remains in flight.

Completion thus refunds only the in-flight token, not the epoch charge. Unlike
older fixtures that retained completed staging until process end, this fixture
calls vkDestroyBuffer/vkFreeMemory, vkDestroyFence/vkFreeCommandBuffers and erases
the completed SubmissionResources, clearing matching page upload pointers first.
Each cycle ends with one live page, zero owned submission objects, zero staging
handles and zero resident **staging payload** bytes. These counts exclude inherited
startup allocations. They do not prove allocator/driver leak freedom. The inherited
helper's incomplete partial-allocation/device-loss cleanup is not exercised or
certified; the tested failures are deliberate pre-allocation rejection and pending
completion rejection with already valid resource owners.

Seven uploads are admitted (initial plus two per cycle); eighteen invalid/admission
or early-completion operations reject. Six actual positive images use independent
original glyph/position CPU composition at the unchanged1e-6 tolerance. Half/full
coverage alternates deterministically; auxiliary outputs retain the inherited
UNUSED/preserve fallback. This is not active MRT or a new font-quality gate.
The outer test rejects a forged early-refund record and a stale image. Validation
is enabled throughout; no illegal use-after-free or malformed GPU request occurs.

Opt in with the existing trusted local toolchain:
```
VULKAN_TEXT18_UPLOAD_BUDGET=1 python -m pytest -c tests/pytest.ini tests/test_text18_upload_budget_lab.py
```
Original files remain unchanged. Actual fence waits and subprocesses are bounded.
Raw receipts stay local; source and minimal numerical summaries may be published.
Target platform performance, full CPU font-service accounting, real Surface and
semantic Live acceptance remain unverified.
