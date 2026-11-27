# Fixed normative-source graph: stage P remains blocked

```sh
python checks19/audit_prose_denominator.py --docs-git /path/to/Vulkan-Docs \
  --output /fresh/source-graph
```

This read-only entry reads the exact Git commit
`fa30d4e312e843193601be7cb926c7e25d9ec885`, tree
`1ef6d54d3efbcf53308f45ccf31d04f61049ea65`: 1,340 ordinary tracked blobs.
It does not read mutable worktree files, execute build scripts, fetch anything,
run Asciidoctor/Ruby, or follow user-selected commands. Git replacement objects and
system/global configuration are disabled. A batch size preflight bounds each blob
and the total before reading payloads. Every tracked path is retained with its
mode, Git object, SHA-256, byte size, coarse category and UNREVIEWED state. Unknown
purpose is explicitly OTHER_UNCLASSIFIED_RETAINED, not exclusion from the source
set. This is complete tracked-source enumeration, not completed normative closure.

All adoc source-local include/conditional directives, attribute definitions and
lines containing attribute macros are retained verbatim with source line/hash.
Nested local condition stacks are lexical context. Inline `ifdef::A[text]` does
not open a stack. Literal includes can resolve only to a tracked file; options
such as `tag=` are retained but not expanded. An include of a tag in the same file
is not classified as an infinite expansion. Attribute-based, generated, remote or
missing targets remain unresolved. Conditions introduced by a parent include are
not propagated. Custom quiet-include, VUID expander and spec macros are inventoried
but not executed or interpreted. No Vulkan/SC/platform configuration is evaluated.

Generation references retain matching build/script lines, not a solved build DAG.
They do not establish generated output correctness, completeness or Reference-page
coverage. Comments, macros and unrecognized build syntax can also match; all full
source hashes remain available for review. XML structure, separate 309 VUIDs,
Headers, SPIR-V and generated-reference closure are not silently unified.

## Substantive existing semantic bridge

The fixed resources.adoc `VkMemoryDedicatedRequirements` refpage, lines
11170–11289, is hashed together with its enclosing line-11169 condition
`VK_BASE_VERSION_1_1,VK_KHR_dedicated_allocation`. Generated struct/validity includes
within the span remain explicit unresolved edges. The manual mapping invokes the
existing `memory_binding_contract19.bind` with three bounded HOST fixtures:
preference alone permits ordinary suballocation, required-but-missing dedication
rejects with the separately frozen 309 coordinate 01444, and matching dedication
at offset zero satisfies that limited contract. Helper and existing test bytes are
pinned and checked before helper import and again afterward. The three controls
reuse the existing contract, not three new independent tests. The test-file digest
is a source binding, not a claim that this CLI runs that pytest module.
These are caller-fact HOST controls, not measured performance, a GPU test,
a device query, authenticated review, or complete binding validity. The 368
paragraph is not claimed byte-equivalent to the 309 VUID corpus.

## Acceptance and stopping point

`P_SOURCE_GRAPH_INDEXED` always accompanies `closure_status: BLOCKED`. Missing
configuration evaluation, include/macro expansion, generated outputs and purpose
review are explicit blockers, even if indexing and all HOST tests pass. Full
reconstruction rejects removed sources, directives, conditions, generation lines,
false resolved edges and a forged COMPLETE status. An incomplete output initially
has BLOCKED_PARTIAL_OUTPUT; only the final summary is the index receipt. The
source-graph file alone cannot establish successful closure.
