# Actual pending atlas lifecycle with scene handoff

This extends the generated joint pipeline, not an aggregation of independent
fixture summaries. On one VkDevice and one queue, **each actual lifecycle render
submission** records one render pass with three ordered draws: opaque full-screen
pre-scene, real packed glyph overlay with the three existing hard fragment clips,
and opaque local post-scene. Color/velocity/ID remain active MRT attachments;
non-target write masks are zero. There is no depth/stencil attachment.

The actual source is the trusted local O bitmap and independent per-glyph pixel
receipt from the earlier fixture. Three fixed destinations and original clipping
predicates remain unchanged. CPU expectations independently compose each clipped
glyph over the scene color, then overwrite the post rectangle [34,54)x[24,40).
No generated Vulkan vertices or readback is used to produce expectations. Both
visible-overlay and post-over-overlay ROIs must be nonzero before the new GPU
pipeline is executed. Tolerance remains 1e-6 and auxiliary sentinels are exact.

The scene image, compatible descriptor and full-quad vertex buffer are separate
from the atlas pages and per-submission glyph vertex buffers. Scene data is
uploaded once in a completed setup submission and remains immutable until all
Engine submissions have finished. Each render submission keeps independent
attachments, readback buffers, command buffer and fence. Scene and glyph stages
explicitly bind compatible pipelines, descriptors, vertex buffers, viewport,
scissor and push constants. The final scene changes viewport/scissor and rebinds
its own pipeline, descriptor and geometry. This proves only these bounded states;
index buffers, depth, stencil, blend constants and arbitrary renderer restoration
are outside scope. Only the glyph overlay is transparent.

The unchanged real lifecycle schedule gates the old-page render at ALL_COMMANDS,
queues candidate B upload behind it, cancels publication while both fences remain
pending, and rejects pending publication/retirement. After signaling and waiting,
an actual retained published-A draw follows. A diagnostic legal draw from the
still-live canceled B descriptor must fail the image oracle. B retires only after
completion, a new generation2 B uploads/publishes, rollback publication is rejected,
and another actual gated render completes before A retires. The gate delays the
whole submission, not proof that the shader is already executing or that queues
run in parallel.

Three positive images each contain three stage draws: 9 verified positive draws.
One wrong-route image adds 3 diagnostic draws, so the main lifecycle has four
render submissions and 12 draws total. Setup scene upload and three atlas uploads
are separate submissions. Preparation fixture results and the separately executed
negative lifecycle are not counted as new joint positives.

A separately compiled legal omission of all five final-state rebindings runs the
same complete lifecycle; its actual image must fail specifically composition,
not validation. A separate controlled exception while A/B are pending verifies
release of the gate, bounded fence wait, cleanup and no validation errors. The
outer test substitutes an old-A readback for new-B and must reject it. These are
not allocation-failure, device-loss, production leak or arbitrary failure proofs.

Opt in `VULKAN_TEXT18_LIFECYCLE_HANDOFF=1` and run:
```
python -m pytest -c tests/pytest.ini tests/test_text18_lifecycle_handoff_lab.py
```
The existing official local toolchain, Vulkan software implementation and trusted
font are required; there is no font redistribution. Calls and fence waits are
bounded. The original real-device, platform and Live acceptance remain unverified.
Raw preparation/tool/driver/source/binary receipts remain local. Only minimal
numerical summaries should be published.
