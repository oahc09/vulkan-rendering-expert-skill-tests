# Resident Scene C integration service

`criteria.md` records inputs and image criteria before the first candidate GPU
execution. This is one bounded integration session, not independent report
aggregation. Python keeps its actual trusted HB/FT provider cache and shelf
packer alive; a resident C++ child keeps both independent Vulkan outputs alive.
CPU F production only occurs after the real A-pending ACK, and F cache reuse
only after canceled B work has completed/retired. Raw trace records order,
provider call deltas and local timestamps. CPU is not fully pre-generated.
It is serial request/response coupling, not parallel font threads or simultaneous
shader execution. Startup helper preparation is separate and not counted.

Initial packing deliberately stores the same O glyph eight times to fill a
page: one unique glyph/eight visible instances. This bounded artificial capacity
pressure is not a deduplicated atlas implementation or packing optimization.
Natural F placement grows actual page count 1→2. Both images remain live; one
renderpass binds page0 for 48 vertices and page1 for 6 vertices, rendering all
nine instances into one output. Old page bytes/UV and submitted vertices remain
immutable. Fresh uncached HB/FT pixels and fixed screen destinations independently
predict transfer/composition; they are not an independent typography algorithm.

Each output has a SceneSnapshot registry. Owner/live/upload-complete/cancel state,
monotonic scene epoch and bounded batches are checked before publication. The
submission copies vertices and batch references, pinning all used pages until
its fence completes. Current-scene pages also cannot retire. CPU face generation
is unchanged in this scenario; scene epochs and native page generations are
separate. GPU success followed by CPU publication is not a distributed atomic
transaction; a failure in that gap aborts with cleanup, not recovery.

A holds the old scene at an actual timeline gate and refuses new draw requests
while paused. B gates its own old snapshot and candidate upload, rejects pending
publication/retirement, then cancels without freeing resident capacity. Only gate
release plus completed fences permits candidate retirement. F hot retry publishes
the new two-page scene while A remains pending. A then releases/readbacks its
old image, is destroyed, and is rebuilt with independent resources; B continues
through both steps. An existing Device handle may be reused after destruction,
but simultaneously live A/B handles must differ. No real Surface is involved.

Both outputs query/enable independentBlend and use three active color attachments.
The shader emits changed auxiliary values, normal write masks preserve them.
Every positive and wrong-page readback checks exact auxiliaries before color.
Seven positive images use unchanged 1e-6, zero exclusions; one legal wrong-page
image must fail composition. A separately compiled bad-write binary repeats the
same resident protocol and all eight images must fail auxiliary preservation,
with validation clean. Pending wrong-sequence and wrong-state processes must
exit nonzero and show both engines' completed bounded cleanup markers. A copied
CANCEL trace falsely claiming released submissions must fail the trace oracle.

CPU max-pages2 overflow is an actual failed prepare with unchanged snapshot and
revision plus unchanged native STATE. Native page cap2 rejects before allocation.
Native submission cap3 is checked before allocation. Tracked native Buffer.size
sums count requested service-owned buffers (staging, vertices, three readbacks),
not allocation alignment/driver memory. Steady points release real resources and
clear uploadSubmission references, not merely counters. Per-output buffer-payload
upper bound 179224 bytes derives from two 12740-byte uploads plus one nine-quad
submission's 864-byte vertices and three 50960-byte readbacks; it is not a product
performance gate. Peak observations are updated after actual page/upload/draw
construction. Inherited helper startup allocations are outside these counters.

CPU glyph-cache coverage clears to zero; two committed packed CPU pages remain
retained (25480 logical float payload bytes), plus uncounted Python metadata and
diagnostic telemetry. Do not interpret either count as total CPU/native heap or
VRAM. Destroyed A's reported live counters are zero because its owner no longer
exists, not because driver-native memory was measured. Arbitrary allocation
failure/device loss/process-crash recovery is not established.

Native input has a 64-byte line budget and absolute 30-second command read
limit. Python ACK limit is 45 seconds, child cleanup wait 45 seconds, actual GPU
fence waits 10 seconds, and the pytest process has its own overall bound.
Wrong sequence/state with pending work are exercised; the elapsed timeout path
itself is bounded in code but not deliberately delayed in this test. Inputs use
sequence-derived local request directories, fixed dimensions and finite values;
foreign handles are rejected before unsafe GPU recording. No arbitrary shell
commands or paths are sent through IPC.

Run with TEXT18_SCENE_C_SERVICE=1 and the existing explicit Vulkan toolchain
configuration. This closes a bounded common Scene C data/lifetime path, not
all language/variation/scale workloads, target platforms, thermal performance,
real Surface or complete original-plan acceptance. No fonts or raw environment
receipts are included in the published minimal numeric report.

A_peak fields belong to the current Output instance lifetime: destruction reports
zero, and rebuilding starts a new instance's high-water counters. They are not
silently a cumulative maximum across A's destroyed/rebuilt lifetimes. The event
series preserves each instance's observations. CPU packed 25480 is logical float
payload accounting, not the Python heap representation of those lists.
Scene snapshots additionally store expected per-page generations independently
of the scene epoch; mismatched page-generation publication is explicitly rejected.
