# Frozen bounded Scene C integration criteria (before candidate GPU execution)

Scope: resident Python HB/FT cache service + one resident C++ process with two
logical Vulkan devices; fixed-size packed page-count growth, not a production
UI engine. All source fonts stay local. Software implementation, offscreen
outputs, not different physical GPUs or real Surfaces.

## Fixed inputs and image oracle

Trusted DejaVu Sans identity and existing provider/cache contracts are unchanged.
O at 20px is 14x15; F at 20px is 10x15 (CPU-only precheck before this GPU run).
ShelfAtlas width65 height49 padding1 max_pages2. Initial batch contains eight
O rectangles: one unique glyph, eight visible instances. Expected placements:
page0 (1,1),(17,1),(33,1),(49,1),(1,18),(17,18),(33,18),(49,18).
The eighth old UV rectangle is [49,18,14,15]. These eight screen destinations
are the same independently frozen coordinates. F then naturally overflows to
page1 at (1,1), not a forced seal or artificial repack. Its screen destination
is (32,34), extent10x15, ending at y49 with zero clipped source pixels. Final
scene: two unique glyphs, nine visible instances, two simultaneously retained
pages sampled with separate descriptors inside one renderpass/submission.

Expected images use independently fresh uncached provider pixels plus the
above fixed screen positions, NOT candidate packed pixels/UV placement. Fresh
shaping receipts match full cached receipts; this is transfer/cache correctness,
not an independent font-quality/shaper certification. All positive color pixels
and ROI use the existing 1e-6 tolerance, zero exclusions. Active velocity and
ID are independently exact before color classification, including negatives.
No depth/stencil/clip contract is added.

## Resident protocol and schedule

1. READY: create A/B devices, query/enable independentBlend, three active MRTs.
2. Only now Python requests actual O cold/hot cache products and packs page0.
   INIT uploads independently on A/B. A submits immutable eight-instance scene
   behind timeline gate and pauses; extra A request is rejected without native
   submission allocation. B draws the old scene. ACK proves A fence NOT_READY.
3. Only after that ACK Python actually requests F (miss), prepares packing
   growth candidate, and sends immutable candidate files. B submits its own old
   snapshot behind B's gate, then candidate upload queues behind it. ACK proves
   both B fences NOT_READY and A still NOT_READY.
4. CANCEL: candidate cannot publish or retire; no pending capacity is returned.
   RELEASE_B opens B gate, waits and reads old snapshot, then retires candidate
   and frees completed submission/staging resources. Python cancels its batch.
5. Python requests F hot (zero HB/FT production), prepares new growth candidate.
   B uploads page1 and publishes a monotonic SceneSnapshot containing page0 old
   UV and page1 F UV, then performs one actual nine-instance/two-descriptor draw.
   A remains pending. Python publishes corresponding CPU batch only after ACK.
6. CPU prepare exceeding max_pages2 must reject with CPU atlas unchanged and
   native STATE before/after equal. CPU cache side effects are not asserted
   transactional. Old page bytes/UV remain unchanged across growth.
7. Release A; its readback still matches old eight O snapshot. Destroy A safely;
   B continues same two-page scene. Rebuild A with independently uploaded current
   two pages and same scene; B continues. Shutdown destroys all tracked objects.

SceneSnapshot checks page owner/live/upload completion/cancel state, epoch and
bounded batch ranges. Submission takes immutable vertex/batch snapshots and
pins every referenced page. Retirement rejects current-scene and pending refs;
not merely the Engine's historical single published-page pointer. Completed
submission objects/staging must actually be freed at declared steady points.

Protocol has fixed opcodes, strictly increasing sequence numbers, bounded input
paths derived from sequence, finite/dimension guards and bounded poll/read/wait.
EOF/timeout or a failure between native commit and CPU publish cleans up after
releasing gates and bounded waits; no cross-process transaction recovery,
arbitrary allocator/device-loss guarantee or process-crash recovery is claimed.

## Negative and accounting evidence

Actual legal wrong-page draw must fail color with auxiliaries intact. An actual
bad-write-mask variant must alter auxiliary images with validation otherwise
clean. No illegal use-after-free or cross-device handle submission. Wrong epoch,
foreign ownership, canceled/pending publication and premature retirement are
rejected before unsafe recording. Trace corruption only modifies a copy.

CPU cache entries/owned coverage, packed-page pixels and staging candidates are
separate from GPU page/submission/buffer/descriptor counts. Fixed limits are
fixture admission capacities, not VRAM, driver leak proof or mobile FPS budgets.
No full pre-generation: receipt timestamps/order and IPC acknowledgements prove
F production occurs after A pending and F hit after canceled B work retires.
Hot CPU hits do not imply skipped GPU uploads. Earlier preparation experiments
are not counted as this service's positive frames.
