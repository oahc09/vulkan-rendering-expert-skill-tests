# Fixed shaped L hard shadow producer/consumer

Actual trusted DejaVu Sans bytes are size/SHA-256 checked before parsing. HarfBuzz
GlyphID 47 (L) drives FreeType line-outline extraction, then a closed 20-triangle
prism, z in [0,6]. Wrong-caster negative uses actual shaped F (41), not a rectangle
standing in for text. Existing provider normalization (height 24) and translation
(.25,.25) are fixed before any GPU run.

One VkDevice per case, two render passes: orthographic light depth draw into a
D32 image, followed by a fullscreen receiver pass sampling that **same image**.
The producer completes a bounded fence wait, and its explicit depth-write to
fragment-read barrier transitions to DEPTH_STENCIL_READ_ONLY_OPTIMAL. There is no
CPU shadow readback/re-upload in between; diagnostic readback happens after the
receiver. Sampled/attachment/transfer format capabilities are queried. Receiver
uses actual descriptor texelFetch, not an uploaded CPU visibility table.

Light projection: (x+.5z,y+.25z), depth z/16. Receiver is a fixed fullscreen plane
parameterized by world (pixel-center.x,pixel-center.y,z=10), not arbitrary receiver
geometry. Light offset (5,2.5) gives integer texel floor indices (pixel.x+5,
pixel.y+3). Out-of-map samples are explicitly lit, not clamped. Bias is fixed zero:
caster z<=6 versus receiver z10 supplies a 4/16 gap. This is hard binary shadow,
not PCF, penumbra, material lighting, or a visible lit caster.

Independent CPU reference ray-intersects the original provider contour caps and
vertical side planes, without consulting generated triangles. Full-map D32 and
full receiver linear RGBA must meet 1e-6, with zero guard/excluded pixels. Active
velocity/ID attachments are protected exactly; receiver D32 .375 is independently
protected but is **not the camera depth of z10**. The helper uses ALWAYS and no
depth write. Every positive/negative checks those protections first.

Actual GPU negatives bypass receiver comparison (producer must remain correct)
and use F instead of L (both producer-depth and receiver color must disagree with
the L oracle). Separate errors are retained. No incorrect output or validation
error is treated as a successful positive. Preparation runs the existing active
MRT fixture separately; those draws are not counted as new shadow evidence.

Local raw evidence includes source/binary hashes and inherited tool/driver/SDK
provenance. First-run missing explicit validation-receipt string is retained in
the local first-run evidence; it was a harness receipt failure, not a changed numerical
threshold. The second run produced passing GPU numbers but failed optional PNG output
because Pillow was absent; the final runner uses a standard-library PNG encoder.
That original evidence remains in the local second-run evidence. No fonts or raw environment fingerprint are published. Same configured
software Vulkan implementation only; not complete Scene B or target hardware.
No claims about arbitrary allocation/device-loss cleanup or production leak freedom.
