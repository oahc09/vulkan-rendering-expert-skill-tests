# Finite straight-stroke true-area AA

This is the next bounded path after hard pixel-center stroke coverage, not a
claim of general AA. Sixteen fixed cases use only horizontal or 3:4 straight
segments, 5px width, butt/square caps, and four diagonal translations of
0/.25/.5/.75 pixels. All resulting rectangle corners are exactly representable
binary fractions. There is no arbitrary input API, join/round/curve/dash AA,
font rasterization, MSAA, or target-device/Live qualification.

GPU fragments compute the actual stroke rectangle intersection with their
pixel square, clip four halfplanes, and use local-coordinate signed area. This
is not a fixed-grid sample approximation. Clipped coordinates explicitly retain
the exact clip-axis bound; line-intersection formulas avoid interpolating that
coordinate away from its boundary. The floating GPU calculations are tested
against an independent exact Fraction reference. CPU reconstruction uses the
original path and rational normalized directions, not uploaded corners. Its
vertical-slice integration splits at vertices and horizontal pixel-boundary
crossings; each interval's clamped height is affine, so rational midpoint
integration is exact. No shared GPU polygon clipping implementation is used.
Host tests independently check total area conservation and known fractional
corner areas. They are marked host_unit.

Conditions are saved before GPU execution. The unchanged composition tolerance
is 1e-6. A 1e-6 coverage-area tolerance is preregistered for this limited exact
rectangle experiment; it is NOT a new global threshold from the original plan.
All pixels are checked, with zero guards/exclusions. Stroke ROI and partially
covered edge pixels are reported separately, so backgrounds cannot dilute the
error. Three adjacent phase transitions in each four-frame group additionally
report coverage-delta error, without inventing another temporal gate.

The shader outputs coverage*0.75 opacity with premultiplied RGB. Real Vulkan
attachment blending is ONE/ONE_MINUS_SRC_ALPHA, for color and alpha. Background
is linear premultiplied (.1,.2,.3,.5); text RGB is (.9,.2,.1). Coverage is inferred
from actual output alpha by (alpha-.5)/.375 and compared with exact area. This is
not an independent separate coverage attachment measurement; all RGBA output is
also checked against CPU linear composition. A single support fragment prevents
polygon-overlap opacity accumulation. Active velocity/ID attachments must retain
their exact sentinels; depth write is disabled and clear depth1 must remain on
every positive and negative draw.

Actual legal negatives replace area with hard-center coverage, or premultiply
RGB by alpha twice. Hard-center must fail coverage and composition; double-alpha
must preserve coverage while failing RGB composition. Validation, auxiliary and
depth preservation cannot be used as substitutes for the intended negative.
The shader is asserted to load as coverage.frag; source/binary/shader hashes and
actual preparation provenance remain local. Subprocess waits are bounded.

The first run exposed inherited mesh depth writes from tiny nonzero clipping
roundoff on a zero-area boundary; it remains in the local first-run evidence.
The new fixture now disables depth writes as designed, explicitly fixes clip-axis
coordinates, and uses implicit-line intersections. No cases, area/composition
tolerances or reference results were relaxed. Prior historical fixtures remain
unchanged. Only source and stripped numerical summary are publishable.

```
VULKAN_TEXT18_STROKE_AREA=1 python -m pytest -c tests/pytest.ini tests/test_text18_stroke_area_lab.py
```

One registered phase, horizontal-square-1, has integer-aligned boundaries and
therefore exactly zero fractional pixels. It is retained as an exact binary
control, not shifted to create an artificial AA result. The second run's
numerical image checks passed, but its initial test incorrectly demanded every
phase have fractional pixels; that assertion is corrected to require zero for
this aligned control and nonzero for the other fifteen phases. All 16 original
cases and the 1e-6 numerical gates are unchanged; the failed run remains local.
