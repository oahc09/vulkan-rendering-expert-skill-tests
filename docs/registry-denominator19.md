# Fixed XML structural denominator

This entry inventories **all XML elements** in the exact Vulkan-Docs commit
`fa30d4e312e843193601be7cb926c7e25d9ec885` vk.xml and video.xml. It does not
complete the original plan's entire normative or semantic denominator.

```sh
python checks19/audit_registry_denominator.py \
  --source-dir /path/to/frozen/Vulkan-Docs/xml --output /fresh/output
```

Both source SHA-256 values are pinned in the helper. No network, build, GPU,
user command, or modification of source XML is performed. The output must be fresh.
Every element, including unrecognized tags, receives an ordered child-index
coordinate, all attributes, text/tail, ancestor attribute context, child coordinates,
and a deterministic subtree hash. Coordinates are XML parser element coordinates,
not byte offsets. Subtree hashes describe the parsed serialization, not a claim of
byte-for-byte XML substring identity. The whole original byte stream is separately
hashed, including comments and processing instructions not represented as elements.

The derived relationship layer preserves require/remove, aliases, structextends
(pNext declarations), type uses, and raw API/platform/protection/stability/dependency
expressions. All other attributes, including future condition attributes, remain
in the exhaustive node layer even if no special relation is extracted. Removing a
condition or unknown node fails full reconstruction verification. Duplicate symbol
names are retained as multiple conditional candidates, not silently collapsed.
Unresolved references may be external/native types or reflect an unsupported
relationship category; they are not automatically classified as specification errors.
Dependencies are **not solved**, remove blocks are **not applied**, pNext validity
is not inferred from a structextends edge alone, and lexical definitions are not
proof of availability, support, enablement or interchangeability.

`alias_applicability` first verifies the whole inventory against pinned bytes and
selects an alias by document/coordinate, never accepting an arbitrary relation. It
is a bounded HOST gate: differing/missing declared API,
API version, Registry revision or condition scopes never establish equivalence. Matching caller-declared
Vulkan 1.4 scopes at Registry revision 1.4.368 plus a unique alias target yield only a structural target observation, not
semantic compatibility or feature enablement. The scopes are declarations, not an
automatic evaluation of XML expressions. No alias result grants runtime authority.

The existing 497 stable Registry scopes remain a distinct review-scope denominator;
this finer structural inventory does not increase their semantic completion. All
new nodes remain UNREVIEWED. Fixed 309 VUIDs are not merged with 368 coordinates.
Expanded prose, Reference material, Vulkan-Headers, SPIR-V and their semantic
cross-version closure remain open. This tool does not produce L1/L2 acceptance.

Tests first verify a complete positive report, then mutate nodes, attributes,
conditions, references and duplicates. Full report verification reconstructs the
inventory from pinned sources, so a re-signed incomplete report is not accepted.
A local fixed-source test explicitly skips when frozen files are unavailable;
that skip is not an executed denominator audit.

SC API version is not fabricated from the Registry revision: this alias gate returns unresolved for SC. Alias chains/cycles are preserved as edges but not solved; unique direct candidates are not a guarantee of acyclic aliases. The CLI exercises a real frozen alias coordinate with matching declared scope and a cross-API refusal.

The CLI is currently POSIX: source leaf symlinks and non-regular inputs are
rejected with O_NOFOLLOW/O_NONBLOCK plus a 16 MB bounded read. Parent directory
resolution is not a sandbox guarantee. Both sources are re-read before output and
again before the success summary. Until the last check, the output summary is
BLOCKED_PARTIAL_OUTPUT; an inventory file alone is not a successful receipt.
Explicit source/target ancestor `api` or `supported` exclusions also block the
alias observation. This is a narrow exclusion check, not dependency evaluation.
