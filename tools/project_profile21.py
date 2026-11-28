"""Capture and reuse reviewed source bindings for an external Vulkan project."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(root):
    return {
        "sha": git(root, "rev-parse", "HEAD").decode("ascii").strip(),
        "tree": git(root, "rev-parse", "HEAD^{tree}").decode("ascii").strip(),
        "changes": git(root, "status", "--porcelain=v1", "--untracked-files=all",
                       "-z").decode("utf-8").split("\0")[:-1],
        "tracked_diff_sha256": digest(git(root, "diff", "--binary", "HEAD", "--")),
    }


def read_binding(root, binding, inputs):
    path = binding["path"]
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path or ":" in path:
        raise ValueError(f"invalid project source path: {path}")
    source = (root / path).resolve()
    if not source.is_relative_to(root):
        raise ValueError(f"source escapes project: {path}")
    row = {"binding": binding, "state": "UNKNOWN"}
    if not source.is_file():
        return dict(row, reason="source missing")
    data = source.read_bytes()
    row["file_sha256"] = digest(data)
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    anchors = binding["anchors"]
    start = 0
    lines = []
    for anchor in anchors:
        if not anchor or text.count(anchor) != 1:
            return dict(row, reason="reviewed anchor missing or ambiguous")
        index = text.find(anchor, start)
        if index < 0:
            return dict(row, reason="reviewed anchors out of order")
        lines.append(text.count("\n", 0, index) + 1)
        start = index + len(anchor)
    if not lines:
        return dict(row, reason="no reviewed anchors")
    return dict(row, state="OBSERVED", lines=lines, inputs=inputs)


def capture(root, config, previous=None):
    root = root.resolve(strict=True)
    if Path(git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve() != root:
        raise ValueError("project root must be the Git checkout root")
    before = identity(root)
    inputs = config["inputs"]
    previous_rows = {}
    if previous and previous["project"] == config["project"]:
        previous_rows = {row["binding"]["role"]: row for row in previous["bindings"]}
    rows = []
    roles = set()
    for binding in config["bindings"]:
        role = binding["role"]
        if role in roles:
            raise ValueError(f"duplicate role: {role}")
        roles.add(role)
        row = read_binding(root, binding, inputs)
        prior = previous_rows.get(role)
        if prior:
            current = {k: v for k, v in prior.items() if k not in {"disposition", "change_reason"}}
            if (current == row and row["state"] == "OBSERVED"
                    and prior["disposition"] in {"INITIAL", "REUSED"}):
                row["disposition"] = "REUSED"
            else:
                row["disposition"] = "REVIEW_REQUIRED"
                row["change_reason"] = "binding, source fingerprint, configuration, or evidence changed"
        elif (inputs.get("reviewed_sha") != before["sha"] or before["changes"]
              or row["state"] != "OBSERVED"):
            row["disposition"] = "REVIEW_REQUIRED"
            row["change_reason"] = "initial binding needs a clean reviewed checkout and observed anchors"
        else:
            row["disposition"] = "INITIAL"
        rows.append(row)
    if before != identity(root):
        raise ValueError("project identity changed during capture")
    for row in rows:
        current = read_binding(root, row["binding"], inputs)
        if current != {k: v for k, v in row.items() if k not in {"disposition", "change_reason"}}:
            raise ValueError("project source changed during capture")
    return {"schema": 1, "scope": "SOURCE_BINDINGS_ONLY", "project": config["project"],
            "checkout": before, "inputs": inputs, "bindings": rows,
            "unknown": config["unknown"], "removed_roles": sorted(previous_rows.keys() - roles)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    print(json.dumps(capture(args.project_root, config, previous), indent=2))


if __name__ == "__main__":
    main()
