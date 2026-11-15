# Existing visibility-temporal output -> HDR-domain UI consumer

Original plan §7.5, not a new TAA implementation. The existing
`hybrid_quality_lab/shaders/temporal.comp` is compiled unchanged. It handles scalar
visibility history, current-to-previous integer pixel displacement, bounds,
depth/class/radiance rejection and neighborhood clamp. This fixture feeds bounded
host-authored diagnostic visibility/depth/class input, not a complete scene
renderer. It does not execute that older fixture's spatial filter: normal GPU
history-save stores accumulated visibility and metadata, not spatial-filter output.

Four registered frames: reset, one-pixel pan, static, reset. Two normal sequences
differ only in frame0 UI O versus F; frame1/3 UI is blank and frame2 F. Real trusted
HB/FT glyph masks are used. Both sequences' entire history and accum buffers must
be byte-identical every frame, proving these UI changes do not enter this history.

Within each sequence all resources share one Device. Actual compute output SSBO
is read by a fullscreen fragment scene mapper (linear RGB=(4,2,1)*(.25+.75*visibility))
then UI draw writes the same RGBA32F target using premultiplied fixed-function
blending. Active velocity/ID and independent depth sentinel remain protected.
A compute->fragment barrier and real SSBO descriptor connect the stages. There is
a diagnostic CPU readback between submissions; those bytes are **not uploaded or
used to feed the GPU consumer**. Subsequent GPU history-save reads accum directly.

The consumer output deliberately stays linear with RGB>1. Diagnostic PNGs apply CPU Reinhard and sRGB only after readback for viewing;
that visualization is not part of the tested GPU output chain. No final tone map,
gamma, PQ encoding or display HDR metadata is claimed. UI ink is fixed linear
(2,3,1), opacity .75. This checks HDR numeric-domain ownership, not an HDR display
or color-management product. World-glyph motion and cache costs remain separate.

Layered gates retain existing values: independent CPU visibility/history reference
at1e-5, consumer formula over verified actual accum at1e-6, and separately reported
CPU-ideal end-to-end error (not silently covered by either). Zero pixel exclusions.
A diagnostic readback used only by the stage-local oracle is explicitly not a
second independent temporal implementation. Source masks/ordered-over math supply
the UI reference; shader outputs are never re-uploaded as expected inputs.

Legal actual GPU negatives: history-save samples the post-UI render target then
applies the inverse scene mapping `(red/4-.25)/.75`. Before future temporal
consumption, frame0 no-UI pixels must match clean history within1e-6 while UI pixels
must differ. The next temporal frame must fail its original reference. This
isolates UI-history contamination instead of an unrelated color-space offset.
The other negative prematurely tone maps the scene, leaving visibility/history
correct but violating the linear consumer contract. Neither is a whole RGB TAA
or complete production render-graph ordering certification.

First execution exposed duplicate destruction of compute pipelines already owned
by the inherited Vulkan helper. The final fixture leaves those registered pipelines
to their owner. Original validation failure evidence is retained locally; no
threshold/input changes were used to hide it. This is not arbitrary device-loss
or allocation-failure cleanup certification. Raw provenance, glyph receipts and
fingerprints stay local; published summary is numerical only. Preparation draws
from the old active-MRT fixture are not counted as this temporal/UI evidence.
