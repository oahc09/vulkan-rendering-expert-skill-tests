#!/usr/bin/env python3
"""No-overwrite build/run evidence; software Vulkan is NOT mobile acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from verify_artifacts import verify, negative_checks

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []

    def run(label, command, timeout=120):
        started = time.monotonic()
        with (out / f"{label}.log").open("x") as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout, cwd=REPO, check=False)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = "TIMEOUT"
        commands.append({"label": label, "command": list(map(str, command)),
                         "returncode": code, "wall_seconds": time.monotonic()-started})
        (out / "commands.json").write_text(json.dumps(commands, indent=2)+"\n")
        return code == 0

    run("git-input", ["git", "status", "--porcelain=v1"])
    run("git-head", ["git", "rev-parse", "HEAD", "HEAD^{tree}"])
    run("compiler-version", [os.environ.get("CXX", "g++"), "--version"])
    run("glslang-version", [os.environ.get("GLSLANG", "glslangValidator"), "--version"])
    run("spirv-val-version", [os.environ.get("SPIRV_VAL", "spirv-val"), "--version"])
    source_files = sorted(p for folder in (HERE, HERE.parent/"engine_scale_lab")
                          for p in folder.rglob("*") if p.is_file()
                          and "build" not in p.parts and "__pycache__" not in p.parts)
    (out/"source-manifest.json").write_text(json.dumps(
        {str(p.relative_to(REPO)): digest(p) for p in source_files}, indent=2)+"\n")
    (out/"environment.json").write_text(json.dumps({k: os.environ.get(k) for k in (
        "VULKAN_SDK_PREFIX", "VK_DRIVER_FILES", "VK_LAYER_PATH", "LD_LIBRARY_PATH",
        "MESA_SHADER_CACHE_DIR", "GLSLANG", "SPIRV_VAL", "CXX")}, indent=2)+"\n")
    built = run("build", [str(HERE/"build.sh"), str(out/"build")])
    passed = False
    overwrite_checks = {}
    if built:
        executable = str(out/"build/hybrid_quality_lab")
        shaders = str(out/"build/shaders")
        normal = run("vulkan-auto", [executable, shaders, str(out/"auto")])
        fallback = run("vulkan-forced-baseline", [executable, shaders,
                                                str(out/"baseline"), "--disable-query"])
        # Prove accidental output reuse is rejected by both entry points.
        def refusal(label, command, target):
            def hashes():
                return {str(p.relative_to(target)): digest(p) for p in sorted(target.rglob("*")) if p.is_file()}
            before = hashes()
            run(label, command)
            after = hashes()
            overwrite_checks[label] = {"before": before, "after": after}
            return (commands[-1]["returncode"] == 1 and
                    (out/(label+".log")).read_text().strip() == "Refuse existing output directory" and
                    before == after and bool(before))
        build_rejected = refusal("reject-existing-build", [str(HERE/"build.sh"), str(out/"build")], out/"build")
        run_rejected = refusal("reject-existing-run", [executable, shaders, str(out/"auto")], out/"auto")
        passed = normal and fallback and build_rejected and run_rejected
    (out/"overwrite-checks.json").write_text(json.dumps(overwrite_checks, indent=2)+"\n")
    (out/"summary.json").write_text(json.dumps({
        "fixture_status": "PASS" if passed else "FAIL",
        "scene_seed": 0, "input_size": [65, 49], "frames": 12,
        "motion": "current_to_previous_pixels_no_jitter_integer_pan",
        "signal": "linear_shadow_visibility_0_1; exposure applied only in composition",
        "query_binary": "little/native-endian float32 RGBA, 65x49",
        "validation": "see each raw Vulkan log; feature and layer availability recorded",
        "coverage_limits": ["software Vulkan is not Android or hardware RT performance",
                            "static AS build only; no GPU update/compaction/retirement stress",
                            "query modes execute initial scene, not temporal query sequence",
                            "no OMM implementation, SDK upscaler, multiview, resize, or deformation",
                            "camera image uses analytic receiver planes; caster depth is rasterized",
                            "LOD/unload/pause lifecycle are reset triggers only, not full lifecycle tests"],
    }, indent=2)+"\n")
    (out/"artifact-manifest.json").write_text(json.dumps(
        {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob("*")) if p.is_file()},
        indent=2)+"\n")
    if passed:
        try:
            result = verify(out)
            result["negative_checks"] = negative_checks(out)
        except (ValueError, OSError) as error:
            passed = False
            result = {"status": "FAIL", "error": str(error)}
            summary = json.loads((out/"summary.json").read_text())
            summary["fixture_status"] = "FAIL"
            (out/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
            manifest = json.loads((out/"artifact-manifest.json").read_text())
            manifest["summary.json"] = digest(out/"summary.json")
            (out/"artifact-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        (out/"verification.json").write_text(json.dumps(result, indent=2)+"\n")
    print(out/"summary.json")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
