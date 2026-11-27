# Pre-registered shared world-text scene core

Scope: one Vulkan Device, one immutable actual shaped L prism vertex buffer,
one actual shaped O grayscale image, one light D32 image, two serial views of
one unchanged world. This is the world-text core of original Scene B, not its
complete vector/stroke/clip/near-plane matrix.

Trusted L=47 and O=50 from the existing size/SHA guarded DejaVu Sans face.
L uses the prior source-outline normalization to height 24 and translation
(.25,.25), z in [0,6]. The SAME mesh is light caster and visible camera geometry.
Light screen=(world.x+.5*z,world.y+.25*z), depth=z/16.
Receiver world plane z=10, opaque warm color, hard shadow factor .25 and bias0.
An ordinary opaque occluder is rectangle [34,43]x[17,28] at z=1.
O label occupies world rectangle [32,46]x[15,30] at z=3, using the complete
trusted 14x15 coverage bitmap without crop or fit. Label LESS and depth-write-off.
Camera A screen=(x+.25*z,y+.125*z); camera B screen=(x-.25*z,y+.25*z).
Both are fixed oblique/shear parallel projections (not orthonormal camera rotations), with distinct ray directions and
same depth order z/16. Viewport65x49, camera depth clear1. No perspective claim.

Light pass first; each view is one camera render pass: receiver, L solid,
ordinary occluder, label. All camera attachments color/velocity/ID active;
only color writes; real scene depth writes for opaque geometry, not label.
One sampled shadow image is consumed directly, not CPU readback/reupload.

Independent CPU oracle intersects original L contour caps/side planes, plane
and rectangle, and samples original O bitmap. Light map expectation is original
contour-ray depth, sampled at floor(light-coordinate), outside map lit. It does
not read generated triangle positions or GPU shadow pixels to form expectations.
All finite whole-image color/depth numerical gates1e-6, zero excluded pixels.
No new visual-quality or performance threshold. Pre-GPU reference must show
nonzero visible L cap/side, receiver shadow, visible and occluded label in both
views; preserve any initial failure, never move scene in response to GPU error.

Negatives: bypass receiver shadow with producer/depth/MRT still correct; cameraB
with only label using cameraA projection, scene/lightdepth/MRT still correct.
Resources remain live until bounded submission completion. No general device-loss
or allocation-failure cleanup, real Surface, hardware, full lighting/material,
bevel, motion or temporal verification claim.
