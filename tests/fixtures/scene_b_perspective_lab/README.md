# Perspective / near / negative object scale in the shared scene

This keeps actual L caster/visible geometry, O label, ordinary receiver/occluder,
and fifth vector panel in each shared camera renderpass. Vertex positions now
use true clip.w=viewZ, not the earlier oblique shear. Camera origins are
(32.5,24.5,-20) and(34.5,24.5,-20), focal40px, viewport65x49. Object reflection is
x'=65-x applied to the SAME source vertices in shadow and visible shaders,
including ordinary meshes and O; it is not a post-render image mirror.

Three complete positive-scene variants: near1 normal, near22 crossing the L prism
viewZ20..26, near1 reflected. Each has a distinct VkDevice and one real light D32
producer, then its twelve camera passes share resources and each has five actual
draws. No cross-variant shared-Device claim. Fifteen positive view outputs plus
21 inherited legal negatives. Two additional deliberately wrong variants exercise
near1 instead of requested22, or missing the reflected caster transform; their
extra inherited variations are diagnostic, not additional positive evidence.

Near22 submits original uncut triangles. Vulkan clips them in homogeneous clip
space; the CPU never clips or pre-rasterizes input. CPU independently intersects
rays with the original contour caps/sides and chooses the closest hit within the
near/far domain, including surviving sides/back after front cap removal. Ordinary
occluder viewZ21 is fully clipped, so zero hidden-label pixels in this variant is
correct. Baseline/reflected variants require both visible/occluded O ROI; crossing
requires visible cap/side and label. Screen-vector overlay remains untransformed.

Fixed-camera sampling is deliberately specialized: gl_FragCoord integer center
rays reconstruct O source texels via integer division, and receiver shadow indices
via fixed plane algebra. Independent CPU uses Fraction ray-plane expressions,
not those reduced integer formulas. The receiver still samples real same-device
D32; no CPU image replaces it. This is not hardware perspective-varying/nearest
certification. Historical nearest boundary failures remain unqualified. No shader
near discard hides missing fixed-function clipping.

## Retained failures and limited stable routes

First hardware-depth run near22/B pixel(42,42) erred1.0312789373e-6, over the
unchanged1e-6. Float32 source-coordinate rounding contributed approximately
4.443e-7; hardware clip/raster depth interpolation added approximately5.870e-7.
The route now explicitly computes gl_FragDepth from perspective-correct world.z
using the SAME projection equation. Geometry, independent ideal source reference,
near plane and tolerance are unchanged. This is neither source-geometry precision
repair nor general hardware-depth acceptance. First-run failure remains local.

First AND second runs also failed reflected/A ordinary rectangle boundary:
pixel-column12 corresponds exactly to source x43, the declared excluded right
edge. Object reflection turns it into a raster-covered physical left edge. The
finite rectangle shader now explicitly enforces its original half-open source
domain using fixed-camera rational coordinates. It does not test near depth.
Discard can only remove excess coverage, not restore omitted samples; full-image
color/depth comparison checks both sides and all interior pixels. Therefore this
is only a verified finite domain fallback, not general mirrored-raster repair.
No pixel exclusion or coordinate movement is used. This corrects the preliminary
claim that all first-run colors passed: mirror/A did not.

## Verification and remaining limits

All positive color/real scene depth/light depth retain1e-6, zero exclusions;
active velocity/ID are checked exactly before other errors. Original seven
negative categories keep correct scene depth and fail color. Wrong-near is an
explicit bad projection configuration and must fail BOTH color and scene depth,
while light remains correct. Wrong-caster-model must fail light depth and color
but preserve camera scene depth. These categories are not interchangeable.

No arbitrary curved near-plane topology, perspective AA/anisotropic-quality,
bevel, general shadow lighting/materials, world-path strokes, real Surface,
target hardware or Live qualification. Full original Scene B still has remaining
scope. Font/tool/build/driver receipts and failures stay local; only source and
stripped numerical evidence are publishable. Existing fixtures are unchanged.

The final exact Fraction edge enumeration also detected an initially omitted
non-reflected A right-edge tie at pixel52. Both A ties (52 normal,12 mirrored)
are the excluded source right edge43; B has no edge centers and no included
left/top edge needs restoration. The erroneous enumeration expectation caused
a separate retained preflight failure, fixed without touching GPU or geometry.
