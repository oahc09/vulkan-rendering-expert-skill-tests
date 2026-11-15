# Same-pass vector panel on the shared world-text scene

This derives a new shared scene executable; old fixtures remain unchanged. One
Device and one real L shadow image serve twelve serial camera passes. Each pass
performs the prior four genuine world draws (receiver sampling light D32, visible
same-buffer L prism, ordinary occluder, actual O label), followed by a fifth
vector draw **inside that same renderpass**. Images are not stitched as joint
proof. Preparation runs historical diagnostics separately and is not counted.

The fifth draw is a full-support quad with a fixed analytic fragment predicate,
not tessellated contour triangles or a CPU-uploaded path mask. Two rectangular
contours form a ring, and a finite straight round-cap stroke is unioned into it.
One premultiplied alpha .35 fragment is blended once over the world scene,
avoiding repeated transparent coverage where stroke and ring overlap. It is hard
pixel-center coverage, not AA or transparent mesh-overdraw correctness.

Five positive views include both cameras with opposite-inner nonzero fill, plus
three full B views: same-inner evenodd, same-inner nonzero, and opposite-inner
evenodd. Same-inner nonzero visibly fills the hole, while the other rules retain
it. The shader uses signed rectangular contour membership/parity; the CPU uses
oriented ray crossings. This is genuine finite rule routing, not a general SVG
parser/winding implementation. CPU stroke uses closest-segment distance; GPU uses
clamped projection/dot algebra. Rectangle, circle and rotated polygon clips
intersect as a three-level stack; GPU halfplanes and CPU finite boundary-plus-
ray-crossing predicates are independent descriptions of the same geometry.

An ALWAYS/non-depth-writing pipeline makes the panel screen-space, retaining
actual world depth unchanged. Three MRT attachments remain active with only color
writable. Every positive and negative independently checks scene depth and exact
velocity/ID before classifying color error. Actual legal negatives bypass each
clip layer, fill the hole, use butt caps, bypass shadow, or use stale label camera.
The old world failures remain observable even after the new panel overlays them.
No validation error substitutes for negative-output detection.

First-run reference failure is preserved: five pixel centers on a rotated clip
edge were included by the original closed GPU halfplane but excluded by new CPU
ray crossing. The CPU now explicitly includes **finite** on-segment points before
winding. No rendering code, geometry, tolerance or guard changed. All five points,
segment endpoints and outside-line extensions have Host tests. Updated preflight
clip differences36/91/35, wrong-hole256, wrong-cap12, path-only297, stroke-only68,
retained-hole256; initial counts and failure are retained in criteria/history.
The historical clip CPU reference already handled finite closed edges correctly;
the omission existed only in this new reference rewrite. This restores the old
contract, not a rendered-quality improvement.

One light producer plus twelve five-draw camera passes. The five positive views
and seven negative views preserve full-frame 1e-6 color/depth, no exclusions.
Light depth is separately checked against source L contour rays. Bitmap/font
quality and pixel-center path quality are not independently certified.

Still NOT complete Scene B: no new curves, rounded frames, joins/dashes, stencil,
AA, negative-scale, near-plane/perspective integration, real Surface or target
hardware/Live. Cameras remain oblique/shear parallel, not rotated orthonormal
perspective cameras. The overlay is not a world-space vector. The same glyph
image is reuploaded each completed view; not upload-once performance. Sources and
stripped numbers may be published; fonts/raw logs/driver paths stay local.
