# Actual cached glyph products → Vulkan page lifecycle

A bounded original Scene C data-path increment, not completion of all Scene C.
The new runner invokes the real font cache, then directly packs returned glyph
coverage into the actual seven atlas inputs consumed by one Vulkan process.
It does not concatenate old reports and call them joint evidence.

Fixed requests are O20/g1, O20/g1, F20/g1, F20/g1, O24/g1, O24/g1,
O20/g2. The g here is CPU face generation; GPU pages independently use initial
0, canceled candidates 1/3/5/7/9/11 and published 2/4/6/8/10/12. Three hot
requests have zero shaping/raster producer calls. A repeated glyph still
uploads to GPU in this experiment; hot cache does NOT imply upload avoidance.
All CPU inputs are generated sequentially before the Vulkan subprocess. This
is not asynchronous CPU/GPU scheduling, nor a provider call made during a
pending GPU draw. Actual CPU generation invalidation is distinguished from
GPU page publication generation.

Each reference is produced by bypassing both caches with the same trusted
HarfBuzz/FreeType provider. Complete shaping receipts are compared; source
pixels/dimensions from this fresh path define the independent cache-transfer
and GPU composition oracle, with fixed glyph destination (8,8). This checks
actual cache product identity and transport, not independent typography quality.
Single glyph bitmap placement intentionally does not reconstruct run layout.

The C++ pending lifecycle is adapted from text_content_churn_lab, using the
unchanged combined lifecycle resource helper. Six cycles each perform gated
old draw, queued candidate upload, cancellation without publication, wait,
old retained draw, candidate retirement, fresh page upload/publication and
new draw. All consumer attachments/vertices/readbacks are independent.
Pending retirement/publication and stale publication are actually rejected.
Completed submission resources are freed; each steady point has one live page,
one page object and zero retained submission objects. This is a fixed-handle
accounting check, not driver leak proof. Cache coverage payload count is a
separate CPU metric and clears to zero before GPU execution.

The principal sequence contains 18 positive draws and 13 uploads. The legal
wrong-resource negative executes a separate full lifecycle with an F atlas
routed into the first O page; O geometry and reference stay unchanged. All
auxiliary attachments are checked before color comparison, including negative
outputs. Another negative modifies only a copy of the real retirement trace
and must be rejected; it does not simulate an illegal GPU destruction.
The oracle requires 1e-6 with no excluded pixels. Auxiliary attachments use the
inherited UNUSED/preserve fallback, NOT the active MRT scenario. Startup helper
preparation draws are not counted as joint evidence.

Limits: single configured software Vulkan implementation/device/queue;
ALL_COMMANDS gate means queued submission is blocked, not shader executing;
fixed 65×49 extent and page replacement, not atlas packing growth; no concurrent
CPU provider, dual Device/Surface, production allocation/device-loss cleanup,
GPU/native memory budget or hardware performance qualification. Existing
separate active MRT/multi-device experiments are not claimed as integrated here.

Opt-in TEXT18_CACHE_CHURN=1 with the established Vulkan SDK/tool environment.
Raw provider hashes, provenance and outputs stay local. Public report is
numeric counts/errors and explicit limitations only. No fonts are uploaded.

The wrong-resource case includes differing F/O bitmap dimensions; it is not an
equal-size glyph or same-layout quality comparison. Bitmap sprites use fixed
top-left placement, not bearings/advances for text layout. Those shaping metrics
are verified against the fresh receipt, but not used to reconstruct a paragraph.
