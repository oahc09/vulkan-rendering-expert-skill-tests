# Frozen perspective / near / object reflection joint scene

All prior world source geometry and fifth screen-vector panel remain unchanged.
Camera origins(32.5+offsetX,24.5,-20), offsetX=0 or2; focal40px, viewport65x49.
True clip.w=viewZ=z+20, clip.z=far/(far-near)*(viewZ-near), far40.
Three complete variants: near1 scaleX+1; near22 scaleX+1; near1 scaleX-1.
Reflection is object model world.x=65-source.x, applied consistently to visible
and shadow vertices, ordinary meshes and label. It is not camera/image mirroring.
Each variant has its own Device; each is the entire same-Device shadow producer,
world camera geometry and vector overlay chain. No across-variant residency claim.

Near22 crosses the L prism viewZ20..26 and completely clips ordinary occluder
viewZ21. Label viewZ23 remains. Original triangle vertices are submitted without
CPU clipping. CPU rays independently choose the nearest hit inside the near/far
interval, including side/back when front cap is clipped.

Fixed-camera O texture reconstruction uses integer pixel center ray coordinates
and texelFetch, not hardware interpolated nearest UV certification. Shader does
not discard on near depth. Receiver plane shadow indices use fixed plane ray
coordinates but consume actual same-device D32. Existing nearest failure remains
historical and is not repaired by this specialized fallback.

Original1e-6 color/depth gates, zero exclusions. Original fill/cap/clip/shadow/
label-camera negatives continue. Added legal wrong-near projection and reflected
visible scene with unreflected shadow producer diagnose integration omissions.
No curved general near topology, perspective AA, real surface/hardware/Live claim.

## Retained numerical diagnostics
First actual run hardware-interpolated depth missed original1e-6 at near22/B
pixel(42,42):1.0312789373e-6. Independent sourcefloat quantization explains
4.4431444548e-7 and remaining hardware projection/interpolation5.8696449182e-7.
An explicit fragment-depth calculation from perspective-correct world.z uses
the identical mathematical projection and leaves fixed-function clipping intact.
It is a specialized reconstruction route, not source-geometry correction or
hardware-depth certification. Independent original source-contour oracle stays.

First and second runs also expose reflected ordinary rectangle's source x=43
boundary at screen x12: geometric reflection changes physical raster edge
ownership. The reference declares original rectangle half-open [34,43), so this
is a separately identified edge-domain discrepancy, not a depth arithmetic one.

The reflected finite rectangle now explicitly enforces its original half-open
source domain using exact fixed-camera integer coordinates. No near rejection is
performed in this shader. Full-image comparison must check both excess and missing
coverage, since discard cannot restore a raster-missed included edge. The second
failure retained the same mirror discrepancy; preliminary 'all colors passed'
was incomplete. Source coordinates, independent oracle and1e-6 remain unchanged.
