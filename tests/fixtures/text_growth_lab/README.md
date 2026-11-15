# Two-page growth, cancellation and retirement integration

Actual Vulkan image-transfer experiment, using the unchanged inflight Lab
initialization. A second independently allocated VkImage represents a candidate
page. This is NOT production atlas packing, resizing an existing image, or an
allocator implementation.

1. Upload generation 0 to the published page and finish its upload fence before
   reusing staging. Allocate a second page.
2. Queue two old-page consumers behind host timeline gates, then the candidate
   generation-1 upload and a diagnostic readback. Mark the candidate canceled:
   host publication stays generation 0. Cancel does not cancel GPU submissions.
3. Release A; B is still gated, so both pages remain alive. Release B, wait the
   canceled upload/readback completion, then execute the published route. Its
   actual readback must still be generation 0, not canceled generation 1.
4. Wait all submission fences, destroy the canceled image and its allocation.
5. Allocate a new second page; upload generation 2 and wait its timeline before
   publishing. The actual route now reads the candidate image. Only after both
   old consumers and all fences have finished is the old page destroyed. The
   new page remains alive until final destructor cleanup.

Five raw readbacks independently verify old A/B, canceled diagnostic data,
post-cancel route and newly published route with exact representable patterns.
The canceled diagnostic read is explicitly not a publication/render consumer.
Tampering the route with canceled bytes or forging canceled publication fails.
An alternate real run throws with old consumers and candidate upload pending;
cleanup releases the final host gate, waits with a 10-second bound, and destroys
the candidate without publication. Child and outer pytest process limits are
120 and 180 seconds. No illegal use-after-free is attempted.

The max two live pages and three creates/two pre-cleanup destroys describe owned
fixture image handles, not driver allocator memory accounting or leak freedom.
The final post-destructor marker and clean validation diagnostics confirm this
controlled cleanup path only. Inherited partial-construction allocation failure,
real device loss, production transaction rollback, growth policy, packing,
fragmentation, multidevice, draw/descriptor consumers and mobile performance are
not covered. Single-queue ordering means candidate transfer execution follows
old consumers; multiple pending submissions are not parallel GPU work.

```
python tests/fixtures/text_growth_lab/run_lab.py --out /new/output
VULKAN_TEXT18_GROWTH=1 python -m pytest -c tests/pytest.ini tests/test_text18_growth_lab.py
```

Use the same explicit compiler/SDK/ICD/validation environment as text_inflight_lab.
No dependencies or fonts are downloaded by the fixture. Validation must be on.
Existing output is refused without mutation. Raw logs and provenance stay local;
only the minimal numerical report belongs in the repository. Previous fixtures
are unchanged.

Recorder page selection uses an RAII slot guard so both success and exceptions
restore the published image handle. A separate actual-initialization run injects
a throw immediately after selecting the candidate, asserts the old slot was
restored and checks validation-clean cleanup. This controlled recorder failure
is not GPU device-loss recovery. Publication/cancellation decisions are host
state; the fixed GPU schedule verifies resulting resource access and lifetimes,
not arbitrary asynchronous application transaction ordering.
