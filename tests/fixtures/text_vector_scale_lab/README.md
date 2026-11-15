# Finite progressive curved-vector triangle draws

Eleven actual Vulkan triangle-list frames use one authored quadratic cap plus
straight closure, scale0.5 through1.125 in1/16 steps, phase0.25. Each frame calls
the existing screen-space flattener/ear-clipper and uploads its actual vertices;
no CPU-premasked texture supplies the shape. Source height/width and viewport
remain finite, with no perspective or clip-plane claims.

Registered before first GPU run: screen flatten tolerance0.125px, conservative
0.25px analytic-boundary guard, linear blend tolerance1e-6 outside that guard.
A separate analytic quadratic predicate predicts the original path, not the
triangulated polygon.1001 analytic curve samples check dense chord error; this
is a finite diagnostic, not a general Bezier error proof. Guard pixels, their
maximum errors and all mismatches are reported explicitly, not silently removed.
Hard center-sample edge ties and tessellation may disagree inside the guard.
These are not antialiased or temporally stable quality results.

The current11frames retain19vertices/17triangles each; screen coordinates and
chord errors change. Do not claim increased topology count or adaptive LOD across
this narrow scale interval. A stale-scale actual readback is rejected against
the later-scale reference. Sentinels use the existing UNUSED/preserve fallback.

First run's GPU and geometry checks passed, but an extra test incorrectly
expected topology count to change at these scales. That test assumption was
corrected to require n-2 triangles. The original cases, numerical limits and
GPU evidence were not changed; the failed first test output is retained locally.

```
VULKAN_TEXT18_VECTOR_SCALE=1 python -m pytest -q -c tests/pytest.ini \
  tests/test_text18_vector_scale_lab.py
```

Preparation reuses the existing mesh and quad controls; preparation draws do not
count as progressive frames. Raw source/tool/font/driver receipts remain under
the prepared local evidence. No production cache, temporal AA, arbitrary contour
set, perspective, extrusion, real-device/Live or full visual acceptance follows.
