# RenderPass vs dynamic rendering: bounded real draw

Run from the Tests repository using the same official tools as preceding cases:

```sh
python cases19/render_organization/run.py --tools /path/to/bin \
 --include /path/to/include --loader /path/to/libvulkan.so.1 \
 --icd /path/to/lvp_icd.json --libdir /path/to/libraries \
 --layerdir /path/to/explicit_layer.d --spec-root /path/to/frozen/Vulkan-Docs \
 --max-renderpass-objects 1 --output /fresh/output
```

Fixed order: RenderPass good → dynamic good → RenderPass recovery → each path's
wrong-output control. Same vertex/fragment SPIR-V, 4×4 RGBA8 single-sample output,
non-symmetric row lengths 1/2/3/1, full 16-pixel independent CPU reference. Both
wrong controls really compare against reversed red/blue expectations and exit6.
These are oracle controls, not injected Vulkan defects or external bugs.

The traditional renderpass initial/final/subpass layout is COLOR_ATTACHMENT_OPTIMAL.
Both paths share explicit UNDEFINED→COLOR_ATTACHMENT and COLOR_ATTACHMENT→TRANSFER_SRC
barriers, copy, transfer-write→host-read dependency and fence retirement. The raw
manifest includes these facts and the actual image allocation flags. The source
records a single submitted draw; no fabricated reuse, concurrency, tile-local-read,
implicit transition or equivalent-pipeline compatibility claims.

Actual object counts are per independently constructed scene, **not per-frame
reallocation**, driver memory or speed. RP/Framebuffer can normally be reused.
Default policy keeps that baseline. `--max-renderpass-objects 0` is an application
management constraint, not an API/physical budget, and selects dynamic only after
both actual output gates pass. `--require-performance` returns NEEDS_MEASUREMENT.
No frame timing, quality beyond this scene, mobile or physical GPU measurement.

The traditional path does not require dynamicRendering enabled or supported. The
complete A/B/A comparison requires both paths; missing dynamic support blocks the
comparison, rather than declaring the legacy path illegal. Actual unsupported
hardware fallback is not demonstrated. The shared attachment validator projection
only reuses shape/format/usage rules: actual path support/enable is checked separately.

Frozen raw368 normative sources and anchors are hash-pinned, not fully preprocessed
specification. VVL309 identity is recorded separately. No API-misuse VUID is claimed.
Tool, header, source, binary/SPIR-V and stdout/stderr hashes are checked again at end.
Provenance records dirty/current heads; this standalone tool is not a clean-pair
release gate. CPU ICD only, no complete C2-family acceptance.
