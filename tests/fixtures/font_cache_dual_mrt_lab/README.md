# Cached glyph data, two logical devices and active MRT

This new same-process execution consumes real CPU cache outputs and enables
three active color attachments on both independent Vulkan devices. It is not a
concatenation of separate dual-device and MRT reports. The preparatory cache
churn runner generates seven actual cached/fresh-reference inputs; its own GPU
draws are tooling preparation and not counted as this stage's evidence.

Shared immutable CPU inputs are the verified hot-hit pages 1/3/5 (O20, F20
and O24), each obtained with zero new HB/FT production, from
that provider cache. Both devices own their own VkImage, descriptors, pipeline,
command buffers, vertices, fences and readbacks. Their VkDevice handles are
checked different while simultaneously live. CPU face-generation and GPU page
publication generation are distinct. This stage consumes the g1 inputs; the
preparation's g2 cache check is not a new dual-device-generation result.

A uploads O20 and submits a draw behind its timeline ALL_COMMANDS gate. An
explicit pause guard refuses new A draw requests before recording/submission,
with unchanged submission object count. B completes O20, uploads then cancels
F20, deliberately renders that still-live canceled page as a wrong-route
negative, then publishes O24 and renders it. Before/after B stages, A's real
fence remains NOT_READY and its timeline counter zero. B cancellation is AFTER
its upload completed, not a claim of a pending B upload. A is explicitly
released, fence-waited and its old O20 image read back before destruction.
B continues with the same device and page; A is reconstructed with a new
logical Device and independent page generation zero and draws F20; B draws
O24 again unchanged. A new handle is required distinct from live B, not from
historically destroyed A (drivers may reuse handle values).

All six positive images are compared to uncached fresh provider pixel
references at the original 1e-6 tolerance, with zero excluded pixels. Glyph
placement is fixed top-left bitmap-sprite placement, not a paragraph layout.
All seven principal images, including the wrong-route image, first require
exact velocity/ID preservation. Color, velocity and ID are ALL active render
attachments. independentBlend is queried and enabled; write masks suppress
auxiliary writes while the shader explicitly outputs different values there.
A separate legal bad-write binary enables those masks: all seven images must
fail the auxiliary oracle without any validation error. Wrong F route has
its own dimensions/placement and is a resource-identity diagnostic, not a
same-size layout comparison.

One primary execution contains six positive and one wrong-route draw; the
bad-write execution repeats seven draws but is not positive evidence. Actual
event counts track B completion and live pages. Cleanup waits are bounded;
validation is checked after all destructors. No arbitrary allocation-failure
or device-loss safety is claimed. Raw binaries, font/provider identities and
logs remain local; published summary contains minimal numeric evidence.

Limits: same configured software Vulkan implementation, not different physical
GPUs or real window Surfaces; no simultaneous shader-execution claim; CPU
products pre-generated, not concurrent CPU/GPU service; fixed pages, no atlas
growth; no depth/stencil/clip in this pipeline; not full original Scene C or
production allocator/leak validation. The two devices do not share GPU handles.

Opt in with TEXT18_CACHE_DUAL_MRT=1 and the established Vulkan tool environment.

The inherited input read helper rejects every nonfinite float before dimensions
and range checks and before any Vulkan object creation. Foreign-page guards
reject publication/draw before recording any cross-device GPU handle.
