# Shared Scene B world-text core (bounded software Vulkan)

This is one genuinely shared scene, not a collage of historical fixture outputs.
Trusted actual HarfBuzz L=47 drives FreeType's single six-edge source contour and
a closed 20-triangle prism. The same vertex buffer is used as a depth shadow
caster and visible camera geometry. Trusted actual O=50 becomes a complete
14x15 grayscale texture region and a depth-tested, non-depth-writing world label.
One VkDevice owns these resources and one D32 shadow image throughout four serial
views. The ordinary receiver and occluder are actual triangle meshes.

The single light producer runs once during construction. Its immutable map is
shared by all four camera passes and read back only after those passes.
The light pass writes D32, then transitions that same image from attachment write
to sampled fragment read. Each camera render pass draws receiver, L prism,
ordinary occluder, and O label. All three color attachments are active; independent
write masks protect velocity and ID. Opaque objects write actual scene depth;
labels use LESS without writing depth. There is no sentinel depth substituted for
camera geometry. Shadow-map readback occurs only after all views and is never
uploaded as a replacement for the producer.

Camera A/B are different oblique/shear parallel projections, not orthonormal
camera rotations and not perspective. They share world geometry, glyph texture,
shadow image, buffers and pipelines. O's image payload is uploaded again into the
same image for each view; no upload-once cache/performance claim. The two negative
views keep scene/light/depth intact but respectively bypass shadow comparison or
use A projection only for the label in B. Both are legal GPU draws. All outputs
first independently check auxiliary attachments and scene depth; color mismatch
cannot hide broken protection. Producer depth is independently checked as well.

Reference ray-intersects the original provider L contour's caps and vertical
sides, rather than generated mesh triangles. It separately intersects receiver,
occluder and glyph planes, samples original O coverage, and computes the shadow
map via original-contour light rays. The reference never consumes GPU depth/color
or generated triangle vertices as its expected image. Fixed CPU preflight requires
visible cap/side, visible shadow, and both visible/occluded nonzero O pixels in
each view, before GPU setup. Full-frame finite size checks and 1e-6 composition,
scene depth and light depth gates have zero exclusions. Shape normalization and
all coordinates were frozen before the first GPU success.

The first preparation failed from nested main macro naming in reused source;
explicit generated-header function renaming fixed this build adaptation, with
original failure retained locally. It did not change geometry, oracle or thresholds.
Preparation executes the old active-MRT diagnostic separately; its outputs are
not counted as shared-scene evidence. The new scene has one light draw and sixteen
camera draws: two positive four-draw views and two negative four-draw views.

This closes a finite world-text core integration, NOT complete Scene B. General
path fill/stroke/nested clip, negative scale, near-plane crossings, perspective,
bevel/material lighting, moving scene/temporal/motion, real Surface, hardware and
Live/device tests are not part of this joint run. Existing independent experiments
are not relabeled joint evidence. Hard nearest shadow/bias0 is not general shadow
quality. No arbitrary allocation/device-loss cleanup or driver leak claim.
Inherited submissions have bounded waits, and outer subprocesses have timeouts.

Run the explicitly opt-in `TEXT18_SCENE_B_SHARED=1` test with the existing official
Vulkan toolchain/validation configuration. Font bytes, raw driver/tool provenance
and generated images stay local. Publish only source and stripped numerical data.
