#!/usr/bin/env python3
"""Reopen evidence and check contents/inventory; never trust summary PASS."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
IGNORED = {"artifact-manifest.json", "verification.json"}
PIXELS = 65 * 49


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and str(p.relative_to(root)) not in IGNORED}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.startswith("{")]


def verify(root):
    root = Path(root)
    manifest = json.loads((root/"artifact-manifest.json").read_text())
    require(manifest == inventory(root), "Artifact inventory/hash mismatch")
    sources = json.loads((root/"source-manifest.json").read_text())
    require(bool(sources), "Missing source hashes")
    for name, sha in sources.items():
        path = (REPO/name).resolve()
        require(path.is_relative_to(REPO) and path.is_file() and digest(path) == sha,
                "Source hash mismatch: " + name)
    commands = json.loads((root/"commands.json").read_text())
    expected = {name: 0 for name in ("git-input", "git-head", "compiler-version",
                "glslang-version", "spirv-val-version", "build", "vulkan-auto",
                "vulkan-forced-baseline")}
    expected.update({"reject-existing-build": 1, "reject-existing-run": 1})
    require(len(commands) == len(expected), "Missing/extra command records")
    require({row["label"]: row["returncode"] for row in commands} == expected,
            "Unexpected command return code (including timeout)")
    refusal = json.loads((root/"overwrite-checks.json").read_text())
    for name in ("reject-existing-build", "reject-existing-run"):
        require((root/(name+".log")).read_text().strip() == "Refuse existing output directory",
                "Wrong refusal diagnostic")
        require(refusal[name]["before"] == refusal[name]["after"] and refusal[name]["before"],
                "Refusal modified old artifacts")
        target = root/("build" if name == "reject-existing-build" else "auto")
        require(refusal[name]["after"] == inventory(target), "Refusal snapshot differs from current files")
    for folder, log in (("auto", "vulkan-auto"), ("baseline", "vulkan-forced-baseline")):
        rows = records(root/(log+".log"))
        require("VALIDATION:" not in (root/(log+".log")).read_text(), "Validation diagnostic")
        final = [r for r in rows if "baseline" in r]
        require(len(final) == 1 and final[0]["baseline"] == "PASS" and
                final[0]["validation_errors"] == 0 and final[0]["frames"] == 12,
                "No valid Vulkan completion record")
        frames = records(root/folder/"frames.jsonl")
        require(len(frames) == 12 and [r["frame"] for r in frames] == list(range(12)),
                "Frame coverage mismatch")
        expected_files = {"frames.jsonl"}
        for row in frames:
            require(all(not isinstance(v, float) or math.isfinite(v) for v in row.values()),
                    "Nonfinite frame metadata")
            require(row["temporal_spatial_oracle_mismatches"] == 0 and
                    0 < row["shadowed_pixels"] < PIXELS and 0 < row["lit_pixels"] < PIXELS,
                    "Invalid frame oracle/coverage")
            require(0 <= row["accepted_history_pixels"] <= PIXELS and
                    (not row["reset"] or row["accepted_history_pixels"] == 0), "Invalid history reset")
            for mode in ("shadow-depth", "raw", "temporal", "filtered", "history-weight", "receiver-depth",
                         "raw-color", "filtered-color"):
                color = mode.endswith("color")
                name = f'frame-{row["frame"]}-{mode}.{"ppm" if color else "pgm"}'
                expected_files.add(name)
                content = (root/folder/name).read_bytes()
                header = b"P6\n65 49\n255\n" if color else b"P5\n65 49\n255\n"
                require(content.startswith(header) and len(content) == len(header)+PIXELS*(3 if color else 1),
                        "Malformed/truncated image: " + name)
        query = [r for r in rows if "query_mode" in r]
        require(len(query) in (0, 2), "Incomplete query modes")
        if folder == "baseline":
            require(not query and any(r.get("forced_baseline") == 1 for r in rows), "Fallback not exercised")
        for row in query:
            require(row["execution"] == "PASS" and row["oracle_mismatches"] == 0 and
                    row["hit_pixels"] > 0 and row["miss_pixels"] > 0 and
                    row["hit_pixels"]+row["miss_pixels"] == PIXELS, "Invalid query oracle")
            name = row["query_mode"]
            expected_files.update({name+".pgm", name+".rgba32f"})
            raw = (root/folder/(name+".rgba32f")).read_bytes()
            require(len(raw) == PIXELS*16, "Truncated query floats")
            require(all(math.isfinite(v) and 0 <= v <= 1 for v in struct.unpack("="+str(PIXELS*4)+"f", raw)),
                    "Nonfinite/out-of-range query floats")
            image = (root/folder/(name+".pgm")).read_bytes()
            require(image.startswith(b"P5\n65 49\n255\n") and len(image) == PIXELS+13, "Malformed query preview")
        require({p.name for p in (root/folder).iterdir()} == expected_files, "Unexpected run file inventory")
    return {"status": "PASS", "checked_files": len(manifest)}


def negative_checks(root):
    """Deliberately corrupt temporary copies; originals are never changed."""
    checks = []
    with tempfile.TemporaryDirectory(prefix="hybrid-verifier-") as tmp:
        copy = Path(tmp)/"evidence"
        for case in ("missing", "extra", "tampered", "nan_with_updated_hash", "wrong_refusal_code"):
            shutil.copytree(root, copy)
            if case == "missing":
                (copy/"auto/frame-0-raw.pgm").unlink()
            elif case == "extra":
                (copy/"auto/unexpected.txt").write_text("unexpected")
            elif case == "tampered":
                (copy/"auto/frame-0-raw.pgm").write_bytes(b"bad")
            elif case == "nan_with_updated_hash":
                path = copy/"auto/frames.jsonl"
                rows = records(path)
                rows[0]["filter_raw_mae"] = float("nan")
                path.write_text("".join(json.dumps(r)+"\n" for r in rows))
                # Keep the refusal evidence internally consistent so this case
                # reaches semantic finite validation, not an earlier hash gate.
                checks_path = copy/"overwrite-checks.json"
                snapshots = json.loads(checks_path.read_text())
                changed = inventory(copy/"auto")
                snapshots["reject-existing-run"] = {"before": changed, "after": changed}
                checks_path.write_text(json.dumps(snapshots))
                (copy/"artifact-manifest.json").write_text(json.dumps(inventory(copy)))
            else:
                path = copy/"commands.json"
                rows = json.loads(path.read_text());rows[-1]["returncode"] = "TIMEOUT"
                path.write_text(json.dumps(rows))
                (copy/"artifact-manifest.json").write_text(json.dumps(inventory(copy)))
            try:
                verify(copy)
            except (ValueError, OSError) as error:
                expected_reason = {
                    "missing": "Artifact inventory/hash mismatch",
                    "extra": "Artifact inventory/hash mismatch",
                    "tampered": "Artifact inventory/hash mismatch",
                    "nan_with_updated_hash": "Nonfinite frame metadata",
                    "wrong_refusal_code": "Unexpected command return code (including timeout)",
                }[case]
                require(str(error) == expected_reason,
                        "Negative verifier case rejected for wrong reason: " + case + ": " + str(error))
                checks.append(case)
            else:
                raise ValueError("Negative verifier case accepted: " + case)
            shutil.rmtree(copy)
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = verify(args.out)
    result["negative_checks"] = negative_checks(args.out)
    print(json.dumps(result))
