# Two logical Vulkan devices: pending-output isolation

One process creates two independent VkInstance/VkDevice/TextLab/Engine objects
using the same configured software Vulkan implementation. The live VkDevice
handles must differ. Their queues, timeline semaphores, descriptor pools, pages,
command buffers, fences, staging, vertices, attachments and readbacks are not
shared. Only immutable CPU atlas/vertex inputs are shared; native copies and file
hashes are compared before/after. This is not different physical GPUs, real
Surfaces, simultaneous shader execution or mobile-device certification.

A uploads/publishes its page and submits a real packed-glyph draw gated at
ALL_COMMANDS with timeline value1 while its counter remains0. Without releasing A,
B actually uploads/publishes/draws its own initial page, cancels an uploaded
candidate, executes a legal wrong-candidate diagnostic draw, then uploads/publishes
and draws generation2. B fence waits complete and images are read back. At all
five registered checkpoints A's fence must still be NOT_READY and its timeline
counter zero. B therefore demonstrates actual independent progress while A waits,
not just a host `paused` Boolean. B candidate cancellation is after its upload
completion and means publication cancellation, not cancellation of GPU commands.

A controlled exception occurs while A is still gated. Its Engine destructor
signals the gate and waits boundedly for submitted work before freeing resources,
then its VkDevice is destroyed. B subsequently performs another real draw with
the retained generation2 page and identical expected output. A's released draw is
not read back, so its final visual output is not claimed; only successful fence
completion and clean bounded destruction are checked. There is no pending GPU
command cancellation or general allocation/device-loss recovery assertion.

A generated owner field guards pages against foreign-device use before any
command recording. Actual CPU attempts to publish and draw A's page through B
are rejected. No invalid cross-device Vulkan submission is performed. The old
fixture files remain unchanged.

Independent original glyph pixels/positions provide the existing linear
premultiplied oracle at1e-6 for B initial, B new and B after A destruction. The
actual canceled-page draw must fail that oracle. An outer negative substitutes
an old readback for new, and another forges the A-pending event. Velocity/ID use
the inherited UNUSED/preserve fallback, not active MRT; no depth is included.
Three positive B images, one B diagnostic image, and one pending A submission
must not be conflated with the separate preparation fixture's results.

Run with the existing trusted Vulkan/font toolchain:
```
VULKAN_TEXT18_DUAL_PENDING=1 python -m pytest -c tests/pytest.ini tests/test_text18_dual_pending_lab.py
```
Engine waits are bounded by10seconds, subprocesses by180seconds and outer test
by300seconds. Error cleanup releases submitted gates before destruction; partial
allocation failure remains outside the tested fault scope. Raw fingerprints and
logs stay local; publish only source and stripped numerical summaries. Original
real-platform and Live acceptance are still unverified.
