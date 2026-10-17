# Vulkan 1.0.9 API manual registry audit (M0)

Audit date: 2026-10-17 UTC. This is an API-knowledge audit of `skill/references/03_api_manual`, not a claim that all prose semantics have been proved. Concurrent editors changed cards during the audit; each scan records its exact per-file input SHA-256. `initial-scan-results.json` preserves the first full scan, not an untouched repository baseline.

## Official source snapshot

Target: Khronos Vulkan-Headers tag **v1.4.365**, Vulkan API **1.4.365**. The original `main` downloads were byte-compared to separately fetched tagged files and all three matched. The embedded valid-usage provenance says spec branch `github-main`, commit `8c9361ba8180c1f4164c0bf79de2f6e817770b0d`, generation date `2026-10-02 01:41:26Z`. That is the embedded spec generation commit, not an independently resolved Vulkan-Headers repository commit.

- [vk.xml](https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/registry/vk.xml), SHA-256 `4ab953836756807a93cee72bc3c63554826b445af43003e0d7d7e876818428ca`
- [vulkan_core.h](https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/include/vulkan/vulkan_core.h), SHA-256 `f331fc8209888d4a6b24d23a6a7baef94d534491ecd3aa0493e4583e505578f0`
- [validusage.json](https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/registry/validusage.json), SHA-256 `e3fe93781fe69c4eda8f4b5464b6aed9a1b7e961e1c6ccd0959e8a9afca4f1e4`

These are data-only downloads; no downloaded executable or package was installed or run.

## Reproduce (Python standard library)

Set ROOT to the exact unpacked Skill repository root (the directory containing `references/03_api_manual`, not its parent), and run the scanner from wherever this report is stored. The scanner exits nonzero if that directory is missing or contains no Markdown files:

```sh
ROOT=/path/to/Skill_Vulkan
SOURCES=$(mktemp -d)
curl --fail --location https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/registry/vk.xml -o "$SOURCES/vk.xml"
curl --fail --location https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/registry/validusage.json -o "$SOURCES/validusage.json"
curl --fail --location https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/v1.4.365/include/vulkan/vulkan_core.h -o "$SOURCES/vulkan_core.h"
sha256sum "$SOURCES/vk.xml" "$SOURCES/validusage.json" "$SOURCES/vulkan_core.h"
# Verify all three hashes against the values above before interpreting the result.
python scan_registry.py --root "$ROOT" --registry-dir "$SOURCES" --vk-xml "$SOURCES/vk.xml" --output registry-scan-results.json
```

Final snapshot paths are relative to the exact Skill repository root, e.g. `references/03_api_manual/...`. The preserved initial snapshot used the original working-parent convention, e.g. `skill/references/03_api_manual/...`; strip that initial `skill/` only when comparing paths. The input content hashes are unchanged by this normalization.

Run the path-contract tests (real root succeeds, parent/wrong root fails, empty manual directory fails):

```sh
python test_scan_registry.py --root "$ROOT" --registry-dir "$SOURCES" --vk-xml "$SOURCES/vk.xml"
```

The scanner never modifies API cards. It extracts `vk*`, `Vk*`, and `VK_*` symbols; checks qualified `Type.member` and `Type::member` references against registered struct members; and looks up concrete full VUIDs in `validusage.json`. Unknowns are triage candidates, not automatic errors. Matching VUID entries include official rule text for manual comparison. The final scanner recognizes numeric suffixes of any length, so a malformed four-digit ID cannot masquerade as a wildcard. Generic VUID families and placeholders remain a separate category.

## Findings and disposition

The initial full snapshot found 48 unique unknown symbol strings. Manual triage identified 20 positive nonexistent/misspelled API references, 23 intentional family/template tokens, two loader layer names outside the registry namespace, one sample local variable, and two explicit negative examples. Earlier transient observations already being corrected by another editor are not represented as a frozen baseline.

The initial snapshot also found 34 distinct missing five-digit VUID references. A later extended scan found one malformed four-digit reference. Each was corrected to a verified rule/ID or to accurate guidance with its official reference page; suffix matching was never treated as a safe replacement rule. **Twelve already-existing VUIDs were separately manually reviewed and found to have materially wrong explanations**: these are preserved in `confirmed-vuid-mismatches.json`, and their explanations were corrected. This semantic check is distinct from lexical existence checking.

Additional targeted corrections covered timeline signal versus wait rules, WSI binary semaphore requirements, dynamic-state field/setter requirements, descriptor-indexing per-type update-after-bind features, and complete reviews of the host-image-copy and maintenance cards. The latter preserve section structure and official references. Host image copy remains optional in Vulkan 1.4, with the official alternative additional-transfer-queue requirement; it was not incorrectly changed to mandatory.

Final results and remaining-token classifications are in `final-summary.json` and `final-symbol-dispositions.json`. No unexplained positive nonexistent API symbols or missing concrete numeric VUIDs remain in this scan. Allowed unknowns include explicit warnings that nonexistent symbols do not exist, loader layer strings, wildcards/templates, and a local variable. This does **not** establish that every narrative claim, unqualified member, code example, platform behavior, extension dependency, or runtime synchronization statement is correct. No Vulkan program was compiled or run by this audit.

## Compact report packaging

Suitable files for `reports/v1.0.9/registry-audit/`:

- README.md
- scan_registry.py
- test_scan_registry.py
- scanner-contract-test-results.txt
- initial-scan-results.json
- final-scan-results.json
- final-summary.json
- final-symbol-dispositions.json
- symbol-dispositions.json
- confirmed-vuid-mismatches.json

Do **not** package `vk.xml`, `vk-tag.xml`, `validusage*.json`, `vulkan_core*.h`, or the mutable intermediate scan in the skill. The source hashes and reproducible tagged-download commands are sufficient. `correct_api_cards.py` is an audit work log helper, not a reusable automatic fixer, and is not needed in release reports.
