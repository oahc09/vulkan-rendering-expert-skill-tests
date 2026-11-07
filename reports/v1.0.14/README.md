# v1.0.14 candidate evidence

This is a **partially validated draft candidate**, not full plan, live-model or Android acceptance. The precise status and limitations are in [acceptance.json](acceptance.json). The plan and fixed upstream source ledger are in `docs/`.

## Revisions and reproduction

Skill: `eff33ec1d8ec726c3978e47f570dd056bfd6d5d3`. Tests executed clean source: `c320b27e62eee7c71923db74098f503cdca49276`. This subsequent commit adds reports only, avoiding a circular report SHA. Check the PR's exact head and CI for the published evidence commit.

- Run `python -m pytest -q tests` beside the pinned Skill checkout: 294 passed, 84 Live skipped.
- Follow `tests/fixtures/hybrid_quality_lab/README.md` to reproduce real shader compilation and software Vulkan. `lab-commands.json` records actual commands and tool versions are preserved.
- The source run verified all 224 generated artifacts and five exact-error negative cases. The portable ZIP excludes only the native executable; read its `PORTABLE-README.txt` and run its `verify_archive.py` for the reduced archive inventory. Do not substitute this reduced verifier for full source-run verification.
- The attached Skill ZIP is one of two byte-identical packages. Both per-file manifests, exact revision, CRC and SHA256 are preserved. Generated files are outside Skill's 200-file runtime whitelist.

## Review and failures

Independent review checked 27 source hashes, all 224 original artifact entries, per-frame finite/history assertions, all five exact-reason negative cases, and both complete RGBA ray-query oracles. Zero oracle mismatches, reset violations or validation errors were observed. Old64 prompt bytes are unchanged; this does not establish semantic nonregression without Live.

Corrected source issues include explicit OMM disable/no-OMM rebuild, query-to-AS-write WAR/compaction edges, motion-vector inverse correspondence, NaN/shape validation, full-channel oracle coverage, exact refusal codes/messages, and no-overwrite hash checks. Prior build/oracle failures are retained in `development-failures/`; they are not hidden as skips.

## Limits

No Live or provider-token target, target host install, Android/hardware performance or power result is available. OMM, AS update/compaction/retirement stress, animated query sequence, GPU multiview/resize/deformation and SDK execution are unfinished. The scene is deliberately small; camera receivers are analytic, actual casters rasterize, and probe fallback is constant. Do not infer visual improvement from a single image or from successful execution. No merge, release, deployment or device certification was performed.
