# P2a: actual official generated fragments, not expanded specification

```sh
python checks19/generate_prose_denominator.py \
  --docs-git /path/to/frozen/Vulkan-Docs --output /fresh/replay
```

This fixed Linux recipe exports all 1,340 ordinary blobs from Docs
`fa30d4e312e843193601be7cb926c7e25d9ec885` into **two separate fresh source trees**.
It invokes the unmodified official `makeSpec -spec core -version 1.4 generated`
with existing `/usr/bin/python3.13`, GNU make and pyparsing. No downloads,
installation, CTS modification, source patch or network include fetch occurs.
The exact commands, compiler-independent tool hashes, pyparsing Python file
hashes, stdout/stderr and owned process-group results are retained.

The official configuration expands to BASE, COMPUTE, GRAPHICS and aggregate
Vulkan versions 1.0 through 1.4, with no enabled extensions. Generated extension
metadata can still exist because official generators emit metadata beyond enabled
core symbols; existence is not enablement. `SPECDATE` is fixed to the source
commit timestamp and `SPECREMARK` explicitly names frozen-source replay. These
are disclosed reproducibility overrides, not the execution wall-clock time or
an upstream source modification. Full generated inventories, including the nine
empty timeMarker files, must match byte-for-byte between the two runs.

Required products include official api, validity, hostsync, metadata, interface,
SPIR-V capability, format, synchronization, dynamic-state fragments, feature
requirements, apimap.py/rb and spec attributes. An explicit core symbol check
covers VkMemoryDedicatedRequirements and its preference/requirement fields.
This is not a claim that every generated symbol has received independent semantic
review. A matching pair of builds alone does not prove generator correctness.

The include observation table independently scans raw tracked adoc sources,
substitutes only explicitly known generated/chapters/appendices prefixes, and
records file existence or missing/unresolved candidates. Options including tags
are preserved. **No conditions or tags are expanded**, so a missing file is not
proved to belong to the active core configuration. Remote or unknown macro paths
are unresolved and never fetched. Likewise, existing files do not establish an
include was actually read by Asciidoctor.

Ruby and Asciidoctor were not available in initial environment preflight. This
recipe does not run HTML, PDF, Reference rendering or validusage generation.
The quiet-include-failure extension belongs to the validusage build path; it is
not described here as the behavior of all HTML builds. `apimap.rb` is Python-
generated text, not evidence of executing Ruby.

Success is `OFFICIAL_CORE14_GENERATED_REPRODUCED_NOT_EXPANDED`, always with
`closure_status: BLOCKED`. Full P closure needs real configuration expansion,
include/tag consumption verification, generated-reference reconciliation and
other required variants. The current limits are not waived by an exit-zero make.

Cancellation and timeouts supervise the complete launched process group. Budget
is 180 seconds after entry preflight starts, checked at stages and in execution;
it is not a hard interruptible deadline for every Python file-hashing operation.
Each make step has a 75-second limit. Interrupted results remain BLOCKED and
preserve logs/completed steps. Retry requires a new output directory.

HOST mutations cover missing products, altered core symbol/configuration,
nonempty markers, injected bytecode/symlinks, altered generated tag bytes and
misleading success labels. They are file/verification controls, not GPU defects.
Original licenses and copyright records remain in both exported source trees.

Execution hardening: the generator interpreter runs with `-S -B`; the existing
pyparsing package's recursive `.py` sources are copied to an isolated dependency
root and supplied via the only PYTHONPATH. No installed package bytecode is used.
An owned dependency probe records the actually imported path and version. Original
and copied package inventories, four implementation files and current Tests HEAD
are rechecked. Both source exports are finally checked for exact bytes, modes and
no extra files outside gen/. This records current implementation provenance, not
a claim of a strict published Skill/Tests pair or all transitive interpreter code.

The actual pre-existing cancel-file control starts zero generator/dependency
steps and returns BLOCKED; reuse of its output directory is rejected. A fresh
recovery reruns both generators. No actual 180-second timeout injection is claimed
for this milestone; timeout cleanup relies on the existing supervisor contract.
