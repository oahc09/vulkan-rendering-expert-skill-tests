# True second camera, same-device serial world-label views

The trusted real O glyph/provider identity, packed atlas and world geometry come
from the unchanged world-label fixture. All four positive views use exactly the
same z=2.75+.25*x plane, original world quad, occluder rectangle, atlas input bytes
and GPU vertex buffer. This is not another distance variation.

CameraA has origin(0,0,0) and identity basis. CameraB has origin(.5,.125,-.25),
right=(24/25,0,7/25), up=(0,1,0), forward=(-7/25,0,24/25), a translation plus
approximately16.26-degree yaw. Vertex push constants contain the full view
matrix; the shader transforms world coordinates before the same actual
perspective projection (near1/far10). CPU independently builds rays from camera
origin and basis, intersects the original glyph/occluder planes, and reads the
original glyph bitmap using nearest reconstruction. It does not read uploaded
matrices, vertices, interpolated UV or GPU pixels to construct expectations.

One TextLab/VkDevice holds one atlas image/descriptor and one world vertex buffer.
LESS/depth-write-off and ALWAYS/depth-write-off label pipelines share the same
layout with an ordinary scene depth-writing pipeline. Each view has a single
render pass with scene then label. CameraA and CameraB each execute depth and
top policies, then a negative executes cameraB scene but stale cameraA only for
the label. 80-byte push constants (ink then mat4 at offset16) are rebound before
each draw with both stage masks. Each submission completes before targets or
readbacks are reused. The unchanged atlas payload is uploaded again for each
view into the same image; this is resource reuse, not an upload-once performance
claim. Input file hashes and the actual GPU vertex-buffer bytes are unchanged.

The four positives use full-frame1e-6 composition/depth gates, no guards. Scene
depth/active velocity/ID preservation is verified independently before interpreting
the stale-label color failure. Both cameras must expose nonzero hidden and visible
glyph ROI; projected hole counts remain reported. The negative cannot qualify by
changing scene projection or failing validation. Three host_unit checks cover
basis orthonormality/actual rotation, view translation and independent ray-plane
intersection. Coordinates and gates are fixed before the first successful run.

This proves a bounded actual second camera on shared resources in serial, not
parallel swapchains/Surfaces, general renderer camera support, shadow rendering
or all SceneB requirements. Real glyph extrusion and shadows remain separate
uncompleted integration obligations. Near crossings are still outside this
fixture's view-depth budget; the dedicated near-clip experiment remains separate.
Nearest aliasing/font quality and target-device/Live qualification are not implied.
Prior preparation runs are not counted among these four positives and one
negative (10 actual scene/label draw calls).

```
VULKAN_TEXT18_SECOND_CAMERA=1 python -m pytest -c tests/pytest.ini tests/test_text18_second_camera_lab.py
```
Raw font/tool/driver/build provenance remains local; only source and stripped
numerical evidence is publishable. Old fixtures are not edited.
