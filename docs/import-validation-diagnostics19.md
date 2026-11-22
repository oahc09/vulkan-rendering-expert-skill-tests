# Import user validation callbacks (read-only)

`checks19/import_validation_diagnostics.py` accepts a user's callback JSON directly;
it does not require a delivery bundle or run any of the five local laboratories.
It never builds/runs the user's project, executes log text, opens embedded URLs,
changes synchronization, applies a patch, or promotes an experience record.

## Input and declaration template

Supported serialized **subset** of `VkDebugUtilsMessengerCallbackDataEXT`:

```json
[
  {
    "pMessageIdName": "VUID-vkUpdateDescriptorSets-None-03047",
    "pMessage": "Original message retained only in your local input file",
    "objectCount": 0,
    "pObjects": []
  }
]
```

The identifier may be null or absent: that record stays UNKNOWN without inventing
an ID or rejecting the other records. Unknown identifiers (including private
UNASSIGNED strings or unsupported SyncVal IDs) are replaced by a neutral marker
and identifier SHA in the output. Only exact corpus VUIDs and the explicit
`SYNC-HAZARD-READ-AFTER-WRITE` allowlist entry are printed verbatim.

`messageIdNumber` is optional int32. Each object requires uint32 `objectType` and
uint64 integer `objectHandle`; optional `pObjectName` is string/null. Handles are
not assigned a generation, source location or submission. Unknown fields, labels
and unsupported serializations are rejected as **unsupported import formats**,
not claimed to be Vulkan violations. Severity/type are callback function arguments,
not fields of CallbackDataEXT; this subset does not ingest them.

The tested CLI is POSIX/Linux-only (`O_NOFOLLOW`, `O_NONBLOCK`, `fstat`); it is not claimed to run unchanged on Windows.

Inputs are UTF-8 regular files, no leaf symlinks/FIFOs, at most 2 MB each (metadata
CLI limit 64 KB), 1,000 callbacks, 64 objects per callback, 16 nested levels and
100,000 JSON nodes. Duplicate keys, nonfinite values and bool-as-integer fields
are rejected. Original message/name/handle values are not copied to reports.

Separate metadata file; every field below is required, but unknowns use null:

```json
{
  "schema": 1,
  "origin": "USER_SUPPLIED",
  "layer_spec": null,
  "settings": {
    "validation": null,
    "sync_validation": null,
    "gpu_assisted": null
  },
  "source_tests_head": null,
  "source_skill_head": null
}
```

`layer_spec` is the encoded **validation-layer** API version, not the device's
API version. For example, 4210997 encodes 1.4.309. This value, settings and historical
revisions remain caller declarations. Nothing here proves which library actually
ran. Missing or mismatched version leaves normative pairing UNKNOWN. The only
accepted normative corpus is the existing pinned 1.4.309 validusage snapshot;
368 prose and registry inventory are not silently substituted.

A deterministic import_id binds callback plus metadata digests, and scopes every evidence_id. It is not a runtime run_id; identical bytes do not prove the same execution. No run/device identity is collected by this importer. Matching revision strings
cannot join separate callbacks into one resource lifetime or authenticated run.
`origin` may additionally be SYNTHETIC_FIXTURE or HISTORICAL_LOCAL_CAPTURE, but those
labels also do not authenticate provenance.

## Command

```sh
python checks19/import_validation_diagnostics.py \
  --callbacks /local/callbacks.json --expected-callback-sha256 CALLBACK_SHA \
  --metadata /local/metadata.json --expected-metadata-sha256 METADATA_SHA \
  --validusage /local/fixed-validusage.json \
  --skill-root /local/paired-skill \
  --expected-tests-head FULL_TESTS_SHA --expected-skill-head FULL_SKILL_SHA \
  --output /fresh/triage
```

Strict mode checks exact clean paired sources and committed helper/route bytes.
Development mode is explicitly labeled and is not a published receipt. Inputs,
source, corpus and knowledge route bytes are rechecked before output. No command,
path or URL from callback/metadata is followed. Output has `report.json` plus inert
`TRIAGE.md`; neither includes original pMessage/object handles/names or input paths.
The report retains JSON pointers and input hashes so the owner can inspect the
original locally. Hashes establish byte integrity, not authenticated provenance.

Exit 0 means only import/review output was produced. It also permits UNKNOWN
lookups and an empty log; neither means the application is correct. BLOCKED input
or source verification returns 2 and produces no successful triage document.

## Three bounded next-step routes

- **03047:** inspect destination binding flags and outstanding consumers; do not
  assume an ordinary binding, update-after-bind exception or premature destruction
  has already been proven.
- **00070:** inspect recording/reset results and invalidating object/descriptor/
  secondary-buffer changes; stale recording is a hypothesis, not the only cause.
- **SyncVal RAW:** identify accesses, ranges and dependency scope; retain shader-
  access heuristic ON/OFF settings. Silent/heuristic-OFF diagnostics and WaitIdle
  workarounds do not demonstrate a repair.

Each route explicitly has unconfirmed mechanism, supporting identifier only,
counterevidence not yet examined, missing evidence/next steps and a stop condition.
Other exact VUIDs receive their conditional specification entries but no invented
root-cause route. Normative text is stripped to text and escaped, conditions remain
unresolved, and source page strings are not made automatic links. No patch,
experiment, external-engine acceptance or full C3/C4 completion is claimed.

HOST tests use explicitly synthetic callbacks. Local historical import evidence
uses already-produced buffer/RAW callback files with their original recorded
Tests/Skill revisions; this does not count as a fresh GPU execution. Raw historical
handles are not vendored into public fixtures or coverage.
