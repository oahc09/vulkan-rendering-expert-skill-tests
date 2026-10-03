#!/usr/bin/env python3
"""Generate v1.0.8 Project Diagnosis responses with an external model command.

The command is provider-agnostic: it must read the complete prompt from stdin
and write only the model response to stdout.

Example:
    VULKAN_SKILL_MODEL_CMD="my-model-wrapper" \
      python tests/run_live_model_behavior.py --check

The wrapper is responsible for authentication and provider-specific arguments.
"""

import argparse
import os
import shlex
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST_REPO = BASE.parent
SKILL_REPO = TEST_REPO.parent / "vulkan-rendering-expert-skill"
PROMPT_DIR = BASE / "prompts"
DEFAULT_OUT = BASE / "responses_v1_0_8_live"

CASES = [
    "tc11_01_repository_map",
    "tc11_02_vulkan_13_upgrade",
    "tc11_03_android_rotation_crash",
    "tc11_04_add_compute_pass",
]

CONTEXT_FILES = [
    "SKILL.md",
    "references/00_expert_entry/hard_rules.md",
    "references/00_expert_entry/response_formats.md",
    "references/00_expert_entry/accuracy_check.md",
    "references/00_expert_entry/verification_gate.md",
    "references/02_core_mental_model/engine_architecture.md",
    "references/02_core_mental_model/regression_reasoning.md",
    "references/05_workflows/01_renderer_setup/project_diagnosis.md",
]


def load_context() -> str:
    if not SKILL_REPO.is_dir():
        raise RuntimeError(
            f"Skill repository not found: {SKILL_REPO}. "
            "Keep both repositories as siblings."
        )
    chunks = []
    for rel in CONTEXT_FILES:
        path = SKILL_REPO / rel
        if not path.is_file():
            raise RuntimeError(f"Required skill context missing: {path}")
        chunks.append(f"\n===== {rel} =====\n{path.read_text(encoding='utf-8')}")
    return "".join(chunks)


def build_prompt(context: str, user_prompt: str) -> str:
    return f"""You are executing vulkan-rendering-expert-skill from the context below.
Follow the Skill rules as authoritative for this test. Do not describe the
test harness. Answer the USER TASK directly.

SKILL CONTEXT:
{context}

===== USER TASK =====
{user_prompt}
"""


def run_model(command: str, prompt: str) -> str:
    proc = subprocess.run(
        shlex.split(command),
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Model command failed ({proc.returncode}):\n{proc.stderr}"
        )
    response = proc.stdout.strip()
    if not response:
        raise RuntimeError("Model command returned an empty response")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--command",
        default=os.environ.get("VULKAN_SKILL_MODEL_CMD"),
        help="Model command that reads prompt from stdin and writes response to stdout",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.command:
        raise SystemExit(
            "Missing model command. Set VULKAN_SKILL_MODEL_CMD or pass --command."
        )

    context = load_context()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for case in CASES:
        prompt_path = PROMPT_DIR / f"{case}.txt"
        if not prompt_path.is_file():
            raise RuntimeError(f"Prompt missing: {prompt_path}")
        user_prompt = prompt_path.read_text(encoding="utf-8")
        full_prompt = build_prompt(context, user_prompt)
        response = run_model(args.command, full_prompt)
        output_path = args.output_dir / f"{case}.md"
        output_path.write_text(response + "\n", encoding="utf-8")
        print(f"{case}: wrote {output_path}")

    if args.check:
        env = os.environ.copy()
        env["VULKAN_BEHAVIOR_RESPONSE_DIR"] = str(args.output_dir.resolve())
        subprocess.run(
            ["pytest", "-q", str(BASE / "test_v1_0_8_model_behavior.py")],
            env=env,
            check=True,
        )


if __name__ == "__main__":
    main()
