# Bounded concave vector triangle lab

Actual software Vulkan triangle-list rendering from an eight-vertex generated
concave U contour and its reflected winding. This is a bounded mesh increment,
not general SVG/font tessellation or 3D extrusion support.

`bounded_vector_mesh.triangulate` uses the existing bounded flattener and simple
contour validation, then ear clipping. It emits indexed triangles with verified
index range, nonzero area, count n-2 and conserved signed area. Holes/multiple
contours explicitly reject to the separately tested CPU mask fallback; they are
never fed through a triangle fan. Production fallback routing is not implemented
by this lab. The 128-segment budget and numerical degeneracy guards are fixed.

The GPU consumes expanded triangle vertices with constant UV and a one-valued
coverage texture. It does not consume a CPU-premasked polygon image. Independent
CPU ray-crossing of the original polygon predicts each pixel center, including
the notch. The contour has integer axis-aligned edges, avoiding ambiguous
edge-center cases. A mirrored transform exercises the opposite winding.

Pre-registered acceptance: linear composition error <=1e-6, all existing
velocity/ID sentinels unchanged, no Vulkan validation diagnostics; triangle area
error <=1e-7 relative and total area 960 square pixels for this fixture. Actual
wrong triangle-fan draws must fail the independent pixel oracle, for both
windings. A copied readback corruption is an additional negative control.

Run with the existing Vulkan/compiler setup:

```
VULKAN_TEXT18_VECTOR_MESH=1 python -m pytest -q -c tests/pytest.ini \
  tests/test_text18_vector_mesh.py tests/test_text18_vector_mesh_lab.py
```

The shared quad pipeline is prepared with its original real-font control; those
separate preparation draws do not count as mesh evidence. The mesh executable
only changes the input divisibility guard from six-vertex quads to triangle
triplets, and retains original vertex bounds/budget and validation behavior.
Raw build/tool/driver provenance resides under `prepared/` locally. Only source
and stripped numerical summaries publish.

Not verified: arbitrary contour sets, hole bridging, curve-to-triangle rendering
quality, antialiasing, stroke/caps, extrusion/bevel, world depth/shadows/second
view, real mobile GPU, Windows/Android providers, Live or production ownership.
