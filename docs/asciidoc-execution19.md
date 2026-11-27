# Actual core Vulkan 1.4 Asciidoctor execution

This fixed Linux recipe extends P2a with actual official HTML rendering and math
postprocessing. It still does **not** complete all P variants, Reference rendering,
validusage generation, Vulkan SC, all extensions, or semantic L1/L2 review.

```sh
python checks19/execute_asciidoc19.py \
  --docs-git /path/to/frozen/Vulkan-Docs \
  --runtime-root /path/to/verified-private-Debian-root \
  --generated-root /path/to/verified-P2a/gen --output /fresh/output
```

The registered source is Docs `fa30d4e312e843193601be7cb926c7e25d9ec885`.
The official Makefile html target runs the original Asciidoctor configuration,
including spec macros, open listings, VUID expansion, Rouge CSS, anchor links,
KaTeX/loadable HTML extensions, and then Node `translate_math.js`. It does not
load quiet-include-failure.rb, which belongs to the separate validusage path.
Core attributes are the exact 20 BASE/COMPUTE/GRAPHICS/aggregate version attributes
from P2a, with no enabled extensions. Source file timestamps are set old in the
isolated copies to reuse the already byte-verified generated inputs without
silently rebuilding them. Source bytes and modes are unchanged.

## Trusted private tool assembly

`tests/fixtures/asciidoc-runtime19.json` registers the 32 Debian package versions
and SHA-256 values, signed release hashes and official keyring hash. Packages were
downloaded from Debian's official 20261103T013555Z snapshot using isolated APT
state/config, checked against package metadata, and extracted with dpkg-deb. No
sudo, system installation, package maintainer scripts, security-setting changes or
new libc/loader injection was used. The private LD_LIBRARY_PATH contains only a
libruby symlink; remaining ELF dependencies resolve from the existing system.

Actual versions: Ruby 3.3.8, Asciidoctor 2.0.23, Rouge 4.5.1; Node 24.22.1 is the
pre-existing interpreter. Debian node-escape-string-regexp 4.0.0-2 and node-he
1.2.0-4 are used with repository KaTeX. This is **not** an npm package-lock
reproduction. It is an explicitly hashed Debian dependency cohort. A different
assembly requires new review and cannot silently reuse the registered tree hash.
Original package licenses/attribution remain in the private extracted root;
upstream Docs licenses remain in every exported source tree.

The report records Ruby/Node ELF ldd paths/hashes, Node module resolution and
loaded module bytes, and Ruby loaded feature paths/hashes. These are bounded
observations, not a claim to capture every possible dynamic-library operation or
all interpreter/OS behavior. The package receipt authenticates the fixed package
sources; an execution trace alone does not authenticate its author.

## Observer and independent comparison

The small Ruby observer prepends four pinned Asciidoctor reader methods and calls
`super`, preserving return values and input data. It records actual conditions,
include resolution and selected strings passed to push_include before original
normalization. Observer-off and observer-on final HTML, including Node math
translation, must match exactly. Both trees' original source bytes/modes and P2a
fragment bytes are rechecked.

The complete observation matrix has a registered normalized digest. Only known
source, private runtime and tool roots are normalized. Counts, all fields and
order remain bound; coordinated edits to selected strings plus their self-hash,
conditions or resolved targets cannot pass merely because HTML is unchanged.
Actual source/resolve/push associations and Ruby loaded bytes are also checked.
This is a **fixed-cohort observation regression**, not an independent general
AsciiDoc condition/tag solver. New versions/configurations need a new cohort.

Tag-selected strings and source hashes are retained. Asciidoctor's start line is
not a complete interval map: its own reader notes that skipped tag lines are not
fully reflected in numbering. We do not invent exact full source intervals from
that start value. No URI-read permission is enabled; non-file include resolutions
are rejected by the observation gate.

## Real controlled counterexamples

Each overlay is a separate copied tree, identified as modified HOST input:
- Remove the active generated VkMemoryDedicatedRequirements include: the actual
  official renderer reports a missing include and fails; arbitrary nonzero exits
  are not sufficient.
- Remove an inactive extension metadata file: core output remains exactly equal.
- Change the fixed line inside a real devsandqueues tag: a separate observer trace
  must show the marker in that tag's selected strings and rendered output changes.
- A separate tiny synthetic engine fixture switches an attribute and confirms
  active versus inactive branch content. It is not an alternate upstream spec.

Before/after path hashes and raw stdout/stderr are retained. These are tool/HOST
controls, not Vulkan/GPU misuse. Corrupted observation reports are separately
covered by tests after a full positive baseline. Historical failed probes remain
failed evidence, including missing Node dependencies and an overly broad initial
string-uniqueness predicate; they are not passed renderer runs.

The entry requires fresh output, fixed sources/tools and owned process-group
supervision. No user command, remote include or arbitrary patch is accepted.
A successful fixed HTML run is a single-configuration milestone, not complete
normative closure or an L1/L2 acceptance upgrade.
