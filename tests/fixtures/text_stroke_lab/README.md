# Bounded opaque polyline strokes: cap/join routing

This screen-space experiment accepts exactly a straight line or a two-segment
polyline, finite width0<width<=8 pixels, butt/square/round caps, and bevel or bounded
miter joins. Curve paths and dash patterns reject explicitly. Nonfinite/negative
width, nonfinite points, zero segments, reversal, bounds and output-triangle
budgets reject before any new GPU setup. The seven exercised rejection cases
must return their exact registered reasons, not an arbitrary exception.

The generator emits segment quads, convex join triangles and cap geometry. Round
caps use64 full-circle segments; the circle overlaps the segment with identical
opaque color. **This proves only an opaque same-color union.** It does not prove
correct half-transparent stroke overdraw or coverage AA. Existing actual Vulkan
mesh drawing uses D32 LESS with all triangles at the same z and active MRT write
protection; overlapping equal-depth/opaque triangles yield the same color.

The independent oracle evaluates original-segment longitudinal/perpendicular
coordinates, analytic circular/end-extension caps, and convex join halfplanes.
It never reads generated triangles. Generator miters intersect offset lines;
reference miters use the angle bisector. Miter ratio means joint-to-tip distance
**divided by half-width**; <=limit keeps miter, >limit falls back to bevel. Fixed
polyline ratio1.825111422437881 is tested against1.5 and3, away from equality.
The unchanged1e-6 tolerance applies to color/depth composition outside a declared
boundary guard; exact auxiliary sentinels remain mandatory everywhere.

The guard is fixed at0.01 pixel before the first GPU run. At maximum radius4,
64-segment cap sagitta is4*(1-cos(pi/64))≈0.00481818px, leaving a fixed0.005px
raster-boundary reserve. The guard is based on every analytic primitive boundary,
including conservative internal union edges, not on observed error pixels.
Every excluded coordinate and its color/depth error, total exclusion count, all-
pixel maximum and unexcluded maximum are reported. Status is
BOUNDED_INTERIOR_PASS, **not full-boundary pixel qualification**. No previous
fixture threshold is changed. The initial sweep already reports0.8 all-pixel
error in the8 guarded pixels of each polyline case; those errors are not hidden
or replaced by interior error. The three straight cap cases exclude zero pixels.

Six positive GPU meshes cover the cap trio, bevel, limited miter and accepted
miter. Two separate legal wrong-output executions use square cap for butt request
and ignore the miter limit. An analytic preflight verifies visible differences
outside both cases' guards before the reviewed GPU sweep; both actual GPU images
must fail the original unexcluded reference, with clean validation and auxiliaries.
No illegal GPU crash or undefined geometry is used. Raw early and reviewed runs
remain local; the preflight addition did not change cases, guard or tolerance.

```
VULKAN_TEXT18_STROKE=1 python -m pytest -c tests/pytest.ini tests/test_text18_stroke_lab.py
```
The old helper sources remain unchanged. Calls/waits are bounded and the existing
local official toolchain is reused. Actual round/miter outputs are inspected.
Source and minimal numerical summaries may be published; raw environment receipts
stay local. No claim covers arbitrary polyline lengths, curves, dashes, SVG/font
stroking, transparent strokes, AA/MSAA, general renderer or target-device/Live
acceptance. Preparation extrusion results are not counted as new stroke evidence.

Six CPU contract tests additionally exercise inclusive miter equality versus the
next lower representable limit, reversal and zero-segment rejection, exact round
triangle budget, output coordinate bounds, and the registered sagitta/reserve
inequality. These do not imply GPU boundary pixels are fully qualified.
