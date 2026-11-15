# Bounded real-content Vulkan churn

Opt in with `VULKAN_TEXT18_CONTENT_CHURN=1` and run
`tests/test_text18_content_churn_lab.py` using the established software Vulkan toolchain.
No fonts downloaded or included. Trusted DejaVuSans is shaped by system HarfBuzz
and rasterized by FreeType; each local receipt includes IDs, positions, size,
direction, language, font and provider hashes. Seven inputs have distinct atlas
hashes: O14, ffi20, Arabic14 RTL, O24(tr), ffi14, Arabic20 RTL, O20.
Language is passed through only: no claim of locale-specific shaping differences.
The inspected 368 TTF/OTF files under `/usr/share/fonts` had no multiple-master
axes; trusted DejaVuSans also has none. Variation is BLOCKED/UNVERIFIED, not PASS.
This scan does not characterize fonts elsewhere in the environment.

The six transitions run in one process on one VkDevice/queue. Every transition
holds a real old descriptor quad draw behind an ALL_COMMANDS timeline gate;
a different-content candidate upload queued behind it is canceled in host routing
while both fences are NOT_READY. Publishing pending/canceled pages and retiring
the pending candidate are rejected before Vulkan destruction. After completion,
a real published-route draw still reads the old content. The candidate is retired,
recreated/uploaded/published at the next generation, and a real new-content draw
is read back. Rollback publishing the old generation is rejected. Only after fences
complete are the old page and all per-submission objects destroyed. Each round
ends with one live page object and zero submission resources; peak live pages is2.
These are owned fixture-object counts, NOT proof of driver allocator leak freedom.

Each page packs one cropped **composited shaped-run bitmap** into a padded region;
actual vertex UV quads sample it. This is not newly validated per-glyph geometry or
full layout. Independent CPU reconstruction uses the original raster pixels and
destination rectangle, not GPU vertices or readback. All18 color images plus
non-target sentinels are verified. Stale-content readback and forged publication
event negative copies must fail without mutating original evidence.

Nearest integer1:1 sampling only. Non-target attachments use the existing
UNUSED/preserve fallback, not active MRT/depth integration. The ALL_COMMANDS gate
proves submitted pending work, not that the shader has begun; single-queue B upload
is blocked behind A, not parallel. Resources are bounded; inherited cleanup opens
the gate then waits10s before destruction, exiting on timeout. Child processes
have120s deadlines and pytest180s. Partial allocation/device-loss failure cleanup
is not comprehensively injected. No production atlas manager, multidevice, mobile,
DirectWrite, MSDF, variable-font or Live acceptance claim.

Preparation invokes the unchanged earlier fixture to produce its graphics helper;
that separate run is not the six-transition evidence. `frames/` and `events.jsonl`
come from the new single-process executable. Tool/driver/source receipts and font
scan details remain local; no raw logs or font files are intended for publication.
