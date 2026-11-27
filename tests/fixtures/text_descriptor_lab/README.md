# Actual sampled descriptor-page draw retirement

One logical Vulkan device, two distinct R32 coverage images, two distinct
immutable combined-image-sampler descriptor sets. Each set is written once and
never updated while in use. Both pages remain alive through draw completion;
publication switches the bound set/page only after the previous fence succeeds.
Two different synthetic coverage patterns produce independently verified RGBA
readbacks. Old resources are destroyed only after submitted consumers finish.

This experiment uses actual fullscreen fragment draws, NOT transfer consumers
standing in for shader descriptor use. Each draw submission waits on a timeline
semaphore value that the host has not yet signaled. vkGetFenceStatus must return
VK_NOT_READY. The host then signals and waits on the actual submission fence
with a 10-second bound. Only afterward may the page binding change or cleanup
occur. A requested controlled abort follows the same signal/wait cleanup path
before propagating failure. Timeout/signal failure exits without entering an
unbounded inherited device-idle destructor. Missing timeline support is failure,
not a simulated fallback. This is a single-queue controlled schedule, not two
simultaneous hardware engines or an application-wide retirement manager.

The runner generates output-only copies of unchanged engine_scale_lab and
text_vector_lab sources: explicitly queries/enables Vulkan12 timelineSemaphore,
increases the text descriptor pool to two sets, substitutes bounded gated
submission hooks, and renames the old entry point. Original fixture files and
all old gates are unchanged. Source replacements fail if expected hook sites
change. Initial host VkEvent experiment was rejected by validation and is NOT
passing evidence; the final implementation uses legal timeline signaling.

The Python oracle derives the two coverage patterns independently rather than
trusting dumped masks, checks every RGBA pixel at fixed 1e-6 linear tolerance,
and verifies untouched non-target sentinels. Negative tests replace new draw
pixels with old-page pixels and forge pending-fence evidence; both fail. Existing
output is refused byte-for-byte unchanged. Validation must be enabled.

```
python tests/fixtures/text_descriptor_lab/run_lab.py --out /new/output
VULKAN_TEXT18_DESCRIPTOR=1 python -m pytest -c tests/pytest.ini tests/test_text18_descriptor_lab.py
```

Use the same explicit official toolchain/ICD environment as text_vector_lab.
Child processes are bounded at 120 seconds; pytest bounds the entire run at 180.
Logs, binary and exact source hashes remain local. Publish only the minimal
numerical summary. This does NOT cover packed-glyph UV extraction, real fonts,
MSDF, descriptor update-after-bind, multi-device/queue integration, mobile GPU
performance, production packing or driver allocator leak freedom. Initialization
allocation failures and true device-loss recovery are not exhaustively injected.

The timeline wait stage is ALL_COMMANDS: NOT_READY proves a real pending
submission, not that shader execution has begun. No overlap/parallelism claim is
made. Compiler/tool versions and hashes, driver/validation manifests, generated
helper hashes and exact repository revisions are saved in local-provenance.json
inside the local output directory only, never in the public numerical report.
