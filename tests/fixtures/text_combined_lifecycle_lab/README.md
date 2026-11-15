# Same-device packed quad lifecycle integration

This is one executable/device/queue, not accumulated PASS results from separate
fixtures. Actual immutable page descriptors feed actual vertex-buffer glyph quad
draws. Explicit PageResources and SubmissionResources own all pages and each
upload/draw's command buffer, fence and relevant staging/vertex/readbacks. Every
draw has separate color/velocity/ID attachments and framebuffer, so pending
submissions never overwrite one another's targets or buffer contents.

The existing packed-quad runner prepares trusted-font O/f/i glyphs, independent
reference pixels, atlas and vertices. Its prior isolated results are prerequisite
checks, not the evidence for the combined flow. The new executable does:

1. Upload A/gen0 and publish only once its fence finishes. Submit A's quad draw
   behind an unsignaled timeline gate.
2. Allocate distinct B/gen1, enqueue its upload, and confirm both A's draw and
   B's upload fences are NOT_READY. Reject pending publication. Cancel B in
   explicit host state; publication stays A. Reject retirement before any
   Vulkan destroy call. Cancellation does not cancel GPU commands.
3. Release the gate; wait both independent fences. Reject publishing B even
   after its upload completes. drawPublished reads the actual published pointer
   to render A again. A legal diagnostic wrong-route draw samples the completed,
   still-live canceled B; the independent image oracle must reject it. Only
   after all consumers finish is B reclaimed.
4. Recreate B/gen2 with half-strength original glyph coverage. Wait its upload,
   publish through the guarded pointer, submit a new gated draw and verify its
   pending fence. Retire that draw, compare its distinct image, then destroy A.

Events derive publication generation and live atlas-page count from real object
state. Independent verification checks the event sequence and three accepted
readbacks. Stale A bytes substituted for new B, forged cancellation publication,
and the actual canceled descriptor route all fail. Each accepted image uses the
original independent glyph/position oracle; gen2 scales source coverage by .5.

An alternate execution throws after A/B are submitted and canceled while still
pending. The owner releases the maximum gate, waits every submitted fence with a
10-second bound, then destroys resources. Cleanup emits a success marker after
its destruction calls and validation checks. The runner additionally rejects any
validation diagnostic during subsequent inherited-device destruction. On wait
or signal failure it exits instead of entering unbounded device-idle cleanup.
Raw logs/source/tool/driver provenance stay local. Fonts are never uploaded.

Limits: ALL_COMMANDS gate proves pending submission, not that a shader started;
single-queue ordering blocks B's upload behind A, not parallel GPU engines.
Nearest 1:1 integer non-overlapping quads only. Non-target attachments use the
older preserved-overlay fallback, NOT the separate active-MRT/depth experiment.
One bounded two-page cycle is not production packing, multithreaded routing,
allocator leak proof, sustained churn or mobile/Windows certification. Existing
helper partial-allocation failures/device-loss cleanup are not comprehensively
RAII-safe or fault-injected; injection occurs only after fully constructed and
submitted resources. The inherited setup has unused general-purpose resources;
`peak_atlas_pages=2` counts actual page objects, not total device allocations.

```
python tests/fixtures/text_combined_lifecycle_lab/run_lab.py \
 --font /trusted/DejaVuSans.ttf --out /new/output
VULKAN_TEXT18_COMBINED=1 python -m pytest -c tests/pytest.ini tests/test_text18_combined_lifecycle_lab.py
```

Use the same explicit compiler/SDK/ICD and trusted font bindings as packed quad.
Child processes are limited to 120s; outer pytest 240s. Missing timeline/validation
support fails. Original fixtures, docs and reports are unchanged.
