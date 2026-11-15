# Actual shaped glyph -> finite geometry or explicit planar fallback

This closes one bounded provider-to-representation routing gap, not all world-text
acceptance. The existing local DejaVuSans file must match its exact759,720-byte
size and SHA256 before any parser is invoked. HarfBuzz actually returns L=47,
O=50 and diagnostic F=41 from that face. FreeType loads each **returned GlyphID**
with NO_SCALE/NO_HINTING/NO_BITMAP; no Unicode value substitutes for a glyph ID.
Provider version, face/font identity and source outlines are recorded locally.

The real L outline has one contour with six line segments. Existing bounded
triangulation accepts it; its actual outline generates front, back and side
triangles with opposite directed incidence for every shared edge. Twenty triangles
are submitted to the existing actual Vulkan oblique-projection mesh path with
D32 LESS/write. The independent CPU ray oracle intersects the original glyph
polygon and its extruded boundary, not generated triangles. Unscaled outline
height24 and a quarter-pixel x/y translation are declared before the new GPU run;
the translation avoids pixel-center boundary ties, not a relaxed error tolerance.
The original1e-6 color/depth tolerance is unchanged. Front and side pixels must
match; the back is submitted but occluded, not independently visible evidence.

O's real outline contains two contours with eight quadratic segments each. The
same restricted triangulator explicitly rejects multiple contours before trying
to invent a filled fan. That decision selects an **actual planar bitmap fallback**:
the same approved face and shaped GlyphID50 are rechecked, FreeType renders the
existing20px hinted grayscale bitmap, and the mask is uploaded/sampled/composited
in Vulkan. Enclosed zero-coverage pixels are identified independently from the
original provider bitmap by exterior flood fill, not from the GPU image; all62
must remain exact background within1e-6. This verifies transport and hole
preservation, not independent font-raster quality.

The fallback has its own explicit existing20px integer baseline/placement and
is flat. It is NOT a same-size/depth/shadow equivalent to the24px normalized solid
mesh, and is not called world-space mask rendering. That scope difference is
reported instead of claiming all representation properties were preserved.
A future production adapter must preserve the requested layout/representation
contract or report its own unsupported condition.

Two legal negative controls actually run: F's real outline produces the wrong
solid for an L request, and a mask with O's enclosed hole forcibly filled produces
a wrong fallback image. Both must fail their original independent references;
auxiliary attachments are checked before accepting wrong-color rejection.
The mesh uses active MRT/depth; the flat bitmap uses its existing UNUSED/preserve
auxiliary fallback. Neither negative uses invalid Vulkan memory or topology.

Only two new positive cases are counted. Preparation fixtures' earlier scenes
and negative test results are not additional new evidence. The actual L and O
images are inspected. Inputs/outputs/source hashes and nested tool/driver receipts
remain local; no font is published. The existing input, segment, vertex and native
buffer budgets are retained. Native waits/subprocesses are bounded.

```
VULKAN_TEXT18_SHAPED_GEOMETRY=1 python -m pytest -c tests/pytest.ini tests/test_text18_shaped_geometry_lab.py
```
Not covered: arbitrary shaped runs/cluster animation, complex mesh holes, bevel,
lighting/shadows/second view, general world labels, real platform or hardware,
semantic Live, and complete font parser/raster certification. No new product
quality threshold or stronger overall completion claim is introduced.
