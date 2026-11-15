# Bounded real near clipping, with explicit stable sampling fallback

Original world-label fixtures remain unchanged. This experiment uploads the
original, uncut trusted O glyph quad; Vulkan clips its homogeneous vertex output.
Camera is clip=(x,y,(10/9)z-10/9,z), near1/far10. The original fixed world rectangle
x[-1,1.25], y[-1.125,1.375] and packed UVs never moved to avoid a failing sample.
Three cases were fixed before the first GPU run:

* cross-near: z=.875+.5*x, corner depths .375..1.5;
* on-near: z=1, exactly the inclusive near boundary;
* behind-near: z=.5+.125*x, all positive w but entirely before near1.

The CPU independently intersects Fraction camera rays with the original plane,
checks 1<=t<=10 and original quad domain, then reads the original cropped glyph
pixels. It does not read GPU vertices or pre-clip geometry. The ordinary scene
rectangle retains its original projection/depth; glyph depth writes remain off,
velocity/ID active attachment write masks stay disabled. Depth and auxiliaries
must pass before any deliberate color-negative interpretation. Full-frame linear
composition/depth tolerance remains1e-6, with zero guards or exclusions.

## Hardware nearest result remains NOT_QUALIFIED

The first actual hardware-nearest cross case differs at pixel(45,10), max color
error .1482353091. An additional actual UV debug readback gave source v
2.999999552965164 versus exact ray result3.0. This is a discontinuous nearest-row
tie after clip/interpolation, not a wrong near clipping boundary. On-near and
behind-near hardware cases pass. All three hardware-nearest outputs are rerun and
reported separately on every invocation; another implementation may have a
different diagnosis. Old failure/debug source/log/readback evidence remains local.
No nearest-interpolation repair or universal rasterization rule is claimed.

## Fixed rational stable sampling route

The fallback still sends the original homogeneous quad through **real Vulkan
clipping**. Only sampling changes: positive-w fragments derive source texels
using bounded exact integer camera/plane expressions and texelFetch on the real
uploaded atlas. GPU sampling performs NO near-plane check or clipping discard.
Thus it cannot conceal a bad fixed-function clip policy.

For fixed cases z=Z/8+(K/8)*x, nx=2*pixelX-64 and ny=2*pixelY-48,
D=520-K*nx. The original rectangle maps to:

* ix=floor(4*glyphWidth*(Z*nx+D)/(9*D));
* iy=floor(glyphHeight*(8*Z*65*ny+9*49*D)/(20*49*D)).

Numerators outside the quad/source domain return zero, rather than access invalid
texels. Every registered pixel/case checks positive denominators and signed32-bit
intermediate bounds before stable shader execution. CPU reference uses unexpanded
Fraction ray-plane arithmetic, not these integer expressions. This is a finite
camera/plane specialization, not a general-purpose replacement for perspective
interpolation. Source font hash, HB GlyphID50, bitmap crop and hole identity remain
locked, with no font redistribution. The three stable outputs must pass1e-6.

Two real legal GPU negative variants clamp **only label** clip.z to max(z,0)
instead of allowing clipping. This does not request an unsupported depthClamp
feature. Packed UVs are strictly positive for label vertices and exactly zero for
scene vertices, asserted before submission as a finite fixture marker. Scene
projection is unchanged. The clamp causes incorrectly visible glyph pixels in
cross and behind cases; original CPU colors must reject them while the same
scene-depth and auxiliary checks pass. Three hardware diagnoses + three stable
positives + two clamp negatives are separate executions, each with an ordinary
scene draw followed by a label draw in one render pass.

Input contract is finite world coordinates and .125<w<9 at every submitted
vertex. Nonpositive w and nonfinite input exercise explicit reason-checked
rejections before output/GPU construction. Affine triangle w extrema occur at
vertices. This does NOT test eye-plane crossings, arbitrary near-plane topology,
far-plane crossing, general camera matrices, shadows, second views, typography
quality or target hardware/Live. Preparation outputs are not new evidence.

```
VULKAN_TEXT18_NEAR_CLIP=1 python -m pytest -c tests/pytest.ini tests/test_text18_near_clip_lab.py
```
Source/minimal numeric reports may be published; raw environment and font
provenance remain local. Historical experiments and thresholds are unchanged.

For reproducibility each run also executes one separate UV-diagnostic draw using
normal perspective interpolation but returning UV directly in RG with alpha1.
At registered pixel(45,10), its actual UV/source coordinates are recorded beside
independent exact Fraction source coordinates; diagnostic depth/aux are still
checked. This extra draw is not a glyph-composition positive or a clip negative.
Hardware summaries retain mismatch counts and the first eight bad coordinates,
explicitly bounded diagnostic samples rather than hidden exclusions.
