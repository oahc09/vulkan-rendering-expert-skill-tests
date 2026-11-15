# Bounded concave solid extrusion

Opt in `VULKAN_TEXT18_EXTRUSION=1` and run `tests/test_text18_extrusion_lab.py`
with the existing Vulkan toolchain. This fixture adds no downloaded dependency.

A single authored U-shaped concave contour is triangulated with the existing
bounded ear clipper. Front z0/back z6 and two triangles per original boundary edge
produce28 real3D triangles (84 xyz+color vertices). Every emitted geometric edge
must have exactly two triangle incidences with one in each directed orientation.
For the CCW source, front reverses the cap triangles to face-z; back retains
CCW to face+z. Side faces keep their outward winding. Back cap is submitted but fully
occluded in the positive fixed view; it is not independently visible proof.

The vertex shader uses a fixed affine oblique projection `(x+z,y+0.5z)` and
Vulkan depth `.2+.05z`. This is not a physically normalized perspective camera.
D32 format attachment/transfer capabilities are queried; real depth comparison
LESS and depth writing enabled. Front/back/side have distinct constant colors,
not lighting. Front and sides are visibly rendered. Actual depth and color are
both read back. Non-target active velocity/ID outputs write different values in
the fragment shader but color write masks preserve their sentinels.

Independent CPU reference intersects each pixel-center ray
`(X-z,Y-0.5z,z)` with the original polygon caps and extruded original edges,
chooses the nearest bounded z, and predicts face color/depth. It does not use
the generated triangles. Predeclared absolute tolerances for all color/depth
samples are1e-6; sentinels exact. Normal and reversed triangle submission order
must both match this reference. An actual valid Vulkan draw with depth testing
disabled must fail the color/depth oracle; an outer pytest copy with corrupted
depth readback is also rejected.

Scope is only this fixed simple concave contour and extrusion. No holes,
multiple contours, bevel, stroke extrusion, dynamic extrusion topology,
world-space lighting, shadow/second-camera view or platform-performance claim.
No AA: fixed sample-center rasterization. Mesh back-face culling remains off.
This demonstrates an actual occluding D32 pipeline, not the prior ALWAYS depth
write-protection test. No generalized 3D-engine integration or Live acceptance.

The independent fixture creates a checked generated helper from the existing
active-MRT lab. Its preparation runs are separate from the extrusion evidence.
Shader validation and runtime Vulkan validation are required, native calls
bounded by120s and outer pytest180s. Raw images/source/tool/driver receipts remain
local. Existing helper allocation/device-loss cleanup limitations still apply.
