# Layout creation, compatibility and push updates: separate contracts

This bounded C1 increment corrects two actual same-card / cross-step contradictions
in `pipeline_layout.md`: different object handles were incorrectly described as
incompatibility, and byte overlap was confused with repeated shader-stage bits.
It does not claim a separate card explicitly stated the opposite.

## Fixed normative mapping

Original clean Khronos Vulkan-Docs commit
`fa30d4e312e843193601be7cb926c7e25d9ec885`, API1.4.368:
- `chapters/descriptorsets.adoc`, SHA256
  `3de692bf6e4f8579de50175be94c564a4580e1b8f0a59ed1e1267e1c3ca88950`;
- explicitly resolved `chapters/commonvalidity/push_constants_common.adoc`, SHA256
  `103dd30346b9483a4c7326b6d49a1444257531577d93ee64ad8a6c14fb377dda`.

Source license CC-BY-4.0, copyright Khronos Group. Three raw section anchors,
physical line ranges and hashes are recorded; the common-validity include is
separately hash-bound. Other includes, conditional compilation and all variant
rules are not implicitly expanded. Pinned1.4.309 VUID references remain separate.

## Rules that matter in real use

1. Pipeline layout handle identity is not compatibility. Descriptor-set
   compatibility for setN depends on identically-defined layouts for **every**
   set0..N, identical push ranges, and matching INDEPENDENT_SETS creation flags.
   Compatible descriptor sets can be bound before binding a pipeline.
2. Push-constant compatibility checks push ranges, not descriptor sets. Compatible
   for push constants is not automatically compatible for any descriptor set.
3. Creation rule00292 prohibits the same stage appearing in two push ranges even
   if the byte ranges are disjoint. Different stages can overlap byte ranges.
4. Valid range creation does not prove a valid update. For every updated byte,
   each requested stage must be covered (01795), and every overlapping range's
   stages must be included by the update (01796). A VERTEX-only update of a region
   overlapped by VERTEX and FRAGMENT ranges is not valid merely because creation
   accepted the layout.
5. Binding descriptor setN can disturb lower bindings with incompatible prefixes;
   if its previous binding was incompatible forN, higher bindings are disturbed.
   This is not the assertion that binding any pipeline automatically destroys
   all descriptor state. The planner models one bind, not all command-buffer state.

## Evidence boundaries

Definition hashes are caller-proven identifiers for identically-defined set
layouts, not handle strings or an automatic Vulkan structure parser. Ordinary
supported facts are validated; unsupported extensions/unknown schema remain
UNKNOWN. Stage/access hardware support, actual shader reflection, real object
creation, command recording and GPU use remain outside the HOST planner.

The source-paired contract examples are positive/negative HOST checks. They are
not new GPU experiments or independent external工程/Live success. Original36
final tasks, full L1/L2 denominator, SC and physical-device gates remain open.

## Reproduce the source-paired HOST controls

```sh
python checks19/run_layout_contracts.py \
  --chapter /path/to/fixed368/chapters/descriptorsets.adoc \
  --common /path/to/fixed368/chapters/commonvalidity/push_constants_common.adoc \
  --validusage /path/to/fixed309/validusage.json --out /fresh/output
```

The entry validates all three original byte hashes before18 registered positive
and negative controls, requires exact expected decisions and disturbance indices,
and records implementation hashes. It does not create real Vulkan handles: two
separate declarations with equal definition hashes model distinct but identical
layouts, while unit controls reject handle-based schema shortcuts. The whole
reported pipeline layout validity remains NOT_INFERRED.
