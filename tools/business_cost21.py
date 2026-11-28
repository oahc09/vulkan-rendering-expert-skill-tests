"""Compare archived business runs against a fixed case plan, without running them."""
import hashlib
import json
import math
from pathlib import PurePosixPath
import re


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_input(root, reference):
    name = reference["path"]
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
        raise ValueError("invalid evidence path")
    path = (root / name).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > 16_000_000:
        raise ValueError("artifact outside evidence directory or over size budget")
    raw = path.read_bytes()
    if sha256(raw) != reference["sha256"]:
        raise ValueError("evidence SHA-256 mismatch")
    return json.loads(raw)


def value(number, label):
    if type(number) not in (int, float) or not math.isfinite(number) or number < 0:
        raise ValueError("invalid " + label)
    return number


def summarize(samples):
    ordered = sorted(samples)
    return {"samples": len(ordered), **{
        name: ordered[math.ceil(q * len(ordered)) - 1]
        for name, q in (("p50", .50), ("p95", .95), ("p99", .99))
    }}


def report(root, manifest, compare):
    """Accept supplied observations only within their predeclared scope."""
    root = root.resolve(strict=True)
    plan_ref = manifest["plan"]
    plan = read_input(root, plan_ref)
    if plan["schema"] != "business-cost-plan-v21":
        raise ValueError("unsupported business cost plan")
    minimum_seconds = value(plan["minimum_seconds"], "minimum_seconds")
    minimum_frames = plan["minimum_frames"]
    registered = plan["registered_unix_ns"]
    limits = plan["max_delta"]
    if (minimum_seconds <= 0 or type(minimum_frames) is not int or minimum_frames < 1
            or type(registered) is not int or registered <= 0 or "frame_p95_ms" not in limits):
        raise ValueError("positive run duration, frame count and frame p95 limit required")
    for metric, limit in limits.items():
        if metric not in {"frame_p50_ms", "frame_p95_ms", "frame_p99_ms", "present_p95_ms"}:
            raise ValueError("decision metric outside bounded comparison")
        value(limit, "maximum regression")
    cases = {case["id"]: case for case in plan["cases"]}
    if len(cases) != len(plan["cases"]):
        raise ValueError("duplicate case identity")
    updates = {case["update"] for case in cases.values()}
    if not {"static", "sparse", "full"} <= updates or not any(
            case["boundary"] in {"multiview", "capacity"} for case in cases.values()):
        raise ValueError("plan must cover static/sparse/full and a view or capacity boundary")

    supplied = manifest["cases"]
    if supplied.keys() - cases.keys():
        raise ValueError("unregistered case")
    used_run_ids = set()
    used_run_hashes = set()
    windows = {}
    rows = []
    for name, case in cases.items():
        scope = case["scope"]
        if any(scope.get(key) is None for key in ("scene", "seed", "camera", "resolution",
                                                 "device", "driver", "cache", "instrumentation",
                                                 "thermal", "power_mode", "quality", "input_sha256")):
            raise ValueError("incomplete comparison scope")
        if not re.fullmatch("[0-9a-f]{64}", scope["input_sha256"]):
            raise ValueError("input requires SHA-256")
        renderers = case["renderer_sha256"]
        paths = case["render_path"]
        if set(renderers) != {"baseline", "candidate"} or not all(
                isinstance(item, str) and re.fullmatch("[0-9a-f]{64}", item)
                for item in renderers.values()):
            raise ValueError("comparison requires pinned baseline and candidate")
        if (set(paths) != {"baseline", "candidate"} or paths["baseline"] != "cpu_instancing"
                or paths["candidate"] not in {"gpu_fixed_slots", "gpu_count"}):
            raise ValueError("comparison paths must use the bounded CPU and GPU paths")
        expected_contracts = ("visible_ids", "image", "capacity", "low_capability")
        actual = supplied.get(name, {})
        correctness = actual.get("diagnostic")
        row = {"case": name, "scope": scope, "comparisons": [], "diagnostic": "NOT_RUN"}
        rows.append(row)
        if not correctness:
            row["decision"] = "NEEDS_MEASUREMENT"
            continue
        diagnostic = read_input(root, correctness)
        if (diagnostic.get("mode") != "diagnostic" or diagnostic.get("plan_sha256") != plan_ref["sha256"]
                or diagnostic.get("case") != name or diagnostic.get("scope") != scope
                or diagnostic.get("renderer_sha256") != renderers or diagnostic.get("render_path") != paths):
            raise ValueError("diagnostic scope differs from plan")
        contract_states = {key: diagnostic.get("contracts", {}).get(key) for key in expected_contracts}
        row.update(diagnostic=contract_states, diagnostic_sha256=correctness["sha256"])
        if any(status != "PASS" for status in contract_states.values()):
            row["decision"] = "KEEP_BASELINE" if "FAIL" in contract_states.values() else "NEEDS_MEASUREMENT"
            continue
        for pair in actual.get("pairs", []):
            arms = {}
            for arm in ("baseline", "candidate"):
                ref = pair[arm]
                run = read_input(root, ref)
                if (run.get("mode") != "business" or run.get("plan_sha256") != plan_ref["sha256"]
                        or run.get("case") != name or run.get("arm") != arm or run.get("scope") != scope
                        or run.get("diagnostic_readback") is not False
                        or type(run.get("business_readback")) is not bool
                        or run.get("renderer_sha256") != renderers[arm]
                        or run.get("render_path") != paths[arm]):
                    raise ValueError("run does not match business scope")
                run_id = run.get("run_id")
                if (not isinstance(run_id, str) or not run_id or run_id in used_run_ids
                        or ref["sha256"] in used_run_hashes):
                    raise ValueError("duplicate or missing run identity")
                used_run_ids.add(run_id)
                used_run_hashes.add(ref["sha256"])
                elapsed = value(run["elapsed_seconds"], "elapsed duration")
                start, end = run.get("started_unix_ns"), run.get("ended_unix_ns")
                if (type(start) is not int or type(end) is not int or start <= registered or end <= start
                        or not math.isclose(elapsed, (end - start) / 1e9, abs_tol=0.001)):
                    raise ValueError("invalid independent run window")
                known_windows = windows.setdefault(scope["device"], [])
                if any(start < other_end and other_start < end
                       for other_start, other_end in known_windows):
                    raise ValueError("run windows overlap on the same device")
                known_windows.append((start, end))
                if type(run.get("failures")) is not int or run["failures"] < 0:
                    raise ValueError("failures must be a nonnegative integer")
                frame_samples = [value(sample, "frame duration") for sample in run["frame_ms"]]
                if type(run.get("captured_frame_count")) is not int or run["captured_frame_count"] != len(frame_samples):
                    raise ValueError("captured frame inventory does not match raw samples")
                if any(sample == 0 for sample in frame_samples):
                    raise ValueError("frame duration must be positive")
                present_samples = run.get("present_interval_ms")
                if present_samples is not None:
                    present_samples = [value(sample, "presentation interval") for sample in present_samples]
                    if any(sample == 0 for sample in present_samples):
                        raise ValueError("presentation interval must be positive")
                frame = summarize(frame_samples) if frame_samples else None
                present = summarize(present_samples) if present_samples else None
                metrics = {f"frame_{key}_ms": frame[key] for key in ("p50", "p95", "p99")} if frame else {}
                if present:
                    metrics["present_p95_ms"] = present["p95"]
                costs = {key: None if run.get(key) is None else value(run[key], key) for key in (
                    "cpu_update_ms", "cpu_record_ms", "cpu_submit_ms", "upload_bytes",
                    "peak_live_bytes", "gpu_critical_ms", "queue_wait_ms",
                )}
                arms[arm] = {"run_id": run_id, "sha256": ref["sha256"], "frame": frame,
                             "presentation": present, "metrics": metrics, "costs": costs,
                             "started_unix_ns": start, "ended_unix_ns": end,
                             "elapsed_seconds": elapsed, "failures": run["failures"],
                             "business_readback": run["business_readback"],
                             "sustained": elapsed >= minimum_seconds and len(frame_samples) >= minimum_frames}
            baseline, candidate = arms["baseline"], arms["candidate"]
            if baseline["failures"]:
                outcome = {"status": "UNVERIFIED_BASELINE"}
            elif candidate["failures"]:
                outcome = {"status": "KEEP_BASELINE"}
            elif (not baseline["sustained"] or not candidate["sustained"]
                    or baseline["business_readback"] != candidate["business_readback"]):
                outcome = {"status": "NOT_COMPARABLE"}
            else:
                outcome = compare(scope | {"metrics": baseline["metrics"]},
                                  scope | {"metrics": candidate["metrics"]}, limits)
                if (outcome["status"] == "WITHIN_DECLARED_LIMITS"
                        and candidate["metrics"]["frame_p95_ms"] > baseline["metrics"]["frame_p95_ms"]):
                    outcome["status"] = "KEEP_BASELINE"
            row["comparisons"].append({"runs": arms, "outcome": outcome})
        statuses = [entry["outcome"]["status"] for entry in row["comparisons"]]
        if "KEEP_BASELINE" in statuses:
            row["decision"] = "KEEP_BASELINE"
        elif len(statuses) >= 3 and set(statuses) == {"WITHIN_DECLARED_LIMITS"}:
            row["decision"] = "WITHIN_DECLARED_MEASURED_SCOPE"
        else:
            row["decision"] = "NEEDS_MEASUREMENT"

    return {"scope": "ARCHIVED_BUSINESS_OBSERVATIONS_ONLY", "plan_sha256": plan_ref["sha256"],
            "cases": rows, "acceptance": "UNVERIFIED", "outside_scope": "NEEDS_MEASUREMENT"}
