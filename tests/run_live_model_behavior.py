#!/usr/bin/env python3
"""Auditable live harness. Wrapper protocol and limitations: see README.md."""
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
TEST_REPO = BASE.parent
SKILL_REPO = Path(os.environ.get('VULKAN_SKILL_ROOT', TEST_REPO.parent / 'skill'))
if not SKILL_REPO.is_dir() and "VULKAN_SKILL_ROOT" not in os.environ:
    SKILL_REPO = TEST_REPO.parent / 'vulkan-rendering-expert-skill'
DEFAULT_OUT = BASE / 'responses_v1_0_9_live'
CASES = [
    'tc11_01_repository_map', 'tc11_02_vulkan_13_upgrade',
    'tc11_03_android_rotation_crash', 'tc11_04_add_compute_pass',
    'tc12_01_invented_sync_enum', 'tc12_02_heap_write_stride',
    'tc12_03_new_sdk_old_android', 'tc12_04_vkprofiles_migration',
    'tc12_05_ahb_descriptor_count', 'tc12_06_apple_tool_matrix',
    'tc12_07_validation_not_correctness', 'tc12_08_blender_proposal',
]
BASELINE_SHA = '1bad967c8e6880c3eecdaa6a946901cbc5c1f060'
# Historical v1.0.8 loading policy, retained ONLY for measured comparison.
BASELINE_CONTEXT_FILES = [
    'SKILL.md', 'references/00_expert_entry/hard_rules.md',
    'references/00_expert_entry/response_formats.md',
    'references/00_expert_entry/accuracy_check.md',
    'references/00_expert_entry/verification_gate.md',
    'references/02_core_mental_model/engine_architecture.md',
    'references/02_core_mental_model/regression_reasoning.md',
    'references/05_workflows/01_renderer_setup/project_diagnosis.md',
]


def digest(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def select_section(text, section=None):
    """Exact Markdown heading including descendants; never silently load whole file."""
    if section is None:
        return text, 1, len(text.splitlines())
    lines = text.splitlines(keepends=True)
    matches = []
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        match = re.match(r'^(#{1,6})\s+(.+?)\s*#*\s*$', line) if not fenced else None
        if match:
            matches.append((i, len(match[1]), match[2]))
    if section.startswith('#'):
        anchor = section[1:]
        anchors = [i for i, line in enumerate(lines)
                   if re.search(r'<a\s+(?:id|name)=[\"\']' + re.escape(anchor) + r'[\"\']\s*></a>', line)]
        found = []
        for position in anchors:
            next_heading = next(((i, level) for i, level, _ in matches if i > position), None)
            if next_heading:
                found.append(next_heading)
    else:
        found = [(i, level) for i, level, title in matches if title == section]
    if len(found) != 1:
        raise ValueError(f'Section must match exactly one heading: {section!r}')
    start, level = found[0]
    end = next((i for i, depth, _ in matches if i > start and depth <= level), len(lines))
    return ''.join(lines[start:end]), start + 1, end


def read_context(root, relative, section=None):
    root = root.resolve()
    if '#' in relative:
        relative, anchor = relative.split('#', 1)
        if section is not None:
            raise ValueError('Specify either path#anchor or section, not both')
        section = '#' + anchor
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path.suffix != '.md' or not path.is_file():
        raise ValueError(f'Invalid skill read: {relative}')
    raw = path.read_bytes()
    selected, start, end = select_section(raw.decode('utf-8'), section)
    return selected, {'path': path.relative_to(root).as_posix(), 'section': section,
                      'start_line': start, 'end_line': end, 'file_sha256': digest(raw),
                      'content_sha256': digest(selected), 'bytes': len(selected.encode('utf-8'))}


def build_prompt(context, user_prompt):
    return ('Execute the Vulkan skill below. Answer in Chinese. Read more skill context as needed.\n'
            'Return JSON with exactly one of: {"read":[{"path":"references/...md",'
            '"section":"exact heading or #explicit-anchor; omit for whole file"}]} or {"answer":"final response"}.\n'
            'Do not fabricate source verification or repository evidence.\n\n'
            + context + '\n===== USER TASK =====\n' + user_prompt)


def run_model(command, prompt, timeout=300):
    return subprocess.run(shlex.split(command), input=prompt.encode('utf-8'),
                          capture_output=True, check=False, timeout=timeout)


def run_case(root, command, model, parameters, case, out, max_rounds=12, timeout=300):
    out.mkdir(parents=True, exist_ok=False)
    record = {'case': case, 'status': 'running', 'reads': [], 'rounds': []}
    write_json(out / 'record.json', record)
    try:
        entry, read = read_context(root, 'SKILL.md')
        (out / 'read-00.txt').write_bytes(entry.encode('utf-8'))
        record['reads'].append(dict(read, round=0, content_file='read-00.txt'))
        context = '===== SKILL.md =====\n' + entry
        user = (BASE / 'prompts' / (case + '.txt')).read_text(encoding='utf-8')
        (out / 'user-task.txt').write_bytes(user.encode('utf-8'))
        record['user_task_sha256'] = digest(user)
        seen = {('SKILL.md', None)}
        for index in range(max_rounds):
            prompt = build_prompt(context, user)
            input_path = out / f'{index:02d}.input.txt'
            input_path.write_bytes(prompt.encode('utf-8'))
            step = {'index': index, 'input_file': input_path.name, 'input_sha256': digest(prompt)}
            record['rounds'].append(step)
            write_json(out / 'record.json', record)
            try:
                proc = run_model(command, prompt, timeout)
            except subprocess.TimeoutExpired as exc:
                for label, partial in [('output', exc.stdout), ('stderr', exc.stderr)]:
                    if partial is not None:
                        raw = partial.encode('utf-8') if isinstance(partial, str) else partial
                        name = f'{index:02d}.{label}.partial'
                        (out / name).write_bytes(raw)
                        step[label + '_partial_file'] = name
                        step[label + '_partial_sha256'] = digest(raw)
                step.update(timed_out=True, timeout_seconds=timeout)
                raise
            output_path = out / f'{index:02d}.output.json'
            output_path.write_bytes(proc.stdout)
            (out / f'{index:02d}.stderr.txt').write_bytes(proc.stderr)
            step.update(output_file=output_path.name, output_sha256=digest(proc.stdout), returncode=proc.returncode)
            if proc.returncode:
                raise RuntimeError(f'Model command failed: exit {proc.returncode}')
            envelope = json.loads(proc.stdout)
            if envelope.get('model') != model or envelope.get('parameters') != parameters:
                raise ValueError('Wrapper model/parameters do not match requested exact configuration')
            usage = envelope.get('usage')
            if not isinstance(usage, dict) or any(
                    type(usage.get(key)) is not int or usage[key] < 0
                    for key in ('input_tokens', 'output_tokens')):
                raise ValueError('Wrapper must provide actual provider input/output token usage')
            step.update(model=envelope['model'], parameters=envelope['parameters'],
                        provider_request_id=envelope.get('request_id'), usage=envelope.get('usage'))
            reply = envelope['response']
            if not isinstance(reply, dict) or (set(reply) not in ({'answer'}, {'read'})):
                raise ValueError('Response must contain exactly answer or read')
            if 'answer' in reply:
                if not isinstance(reply['answer'], str) or not reply['answer'].strip():
                    raise ValueError('Empty model answer')
                (out / 'answer.md').write_bytes(reply['answer'].encode('utf-8'))
                record.update(status='generated', answer_sha256=digest(reply['answer']))
                return record
            requests = reply['read']
            if not isinstance(requests, list) or not 1 <= len(requests) <= 8:
                raise ValueError('Expected 1..8 read requests per round')
            for request in requests:
                relative, section = request['path'], request.get('section')
                text, read = read_context(root, relative, section)
                key = (read['path'], read['section'])
                if key in seen:
                    raise ValueError(f'Duplicate read: {key}')
                seen.add(key)
                content_file = f"read-{len(record['reads']):02d}.txt"
                (out / content_file).write_bytes(text.encode('utf-8'))
                record['reads'].append(dict(read, round=index + 1, content_file=content_file))
                context += f'\n===== {read["path"]} | {read["section"] or "whole file"} =====\n{text}'
            write_json(out / 'record.json', record)
        raise RuntimeError('Maximum retrieval rounds reached without answer')
    except Exception as exc:
        record.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        write_json(out / 'record.json', record)


def audit_case(folder, manifest):
    """Verify delivered bytes, read requests and the complete cumulative transcript."""
    record = json.loads((folder / 'record.json').read_text())
    assert record['status'] == 'generated'
    task = (folder / 'user-task.txt').read_text(encoding='utf-8')
    assert digest(task) == record['user_task_sha256']
    reads = record['reads']
    assert reads and reads[0]['path'] == 'SKILL.md' and reads[0]['round'] == 0
    chunks = []
    for read in reads:
        chunk = (folder / read['content_file']).read_bytes()
        assert digest(chunk) == read['content_sha256']
        assert len(chunk) == read['bytes']
        chunks.append(chunk.decode('utf-8'))
    assert record['rounds']
    consumed = 1
    context = '===== SKILL.md =====\n' + chunks[0]
    final = None
    for index, step in enumerate(record['rounds']):
        assert step['index'] == index
        raw_input = (folder / step['input_file']).read_bytes()
        assert digest(raw_input) == step['input_sha256']
        assert raw_input.decode('utf-8') == build_prompt(context, task)
        raw = (folder / step['output_file']).read_bytes()
        assert digest(raw) == step['output_sha256']
        output = json.loads(raw)
        assert output['model'] == step['model'] == manifest['model']
        assert output['parameters'] == step['parameters'] == manifest['parameters']
        assert output['usage'] == step['usage']
        assert all(type(step['usage'][key]) is int and step['usage'][key] >= 0
                   for key in ('input_tokens', 'output_tokens'))
        assert step['returncode'] == 0
        reply = output['response']
        if 'answer' in reply:
            assert index == len(record['rounds']) - 1
            final = reply['answer'].encode('utf-8')
        else:
            for request in reply['read']:
                read = reads[consumed]
                relative, section = request['path'], request.get('section')
                if '#' in relative:
                    relative, anchor = relative.split('#', 1)
                    section = '#' + anchor
                assert Path(relative).as_posix() == read['path']
                assert section == read['section'] and read['round'] == index + 1
                context += f'\n===== {read["path"]} | {read["section"] or "whole file"} =====\n{chunks[consumed]}'
                consumed += 1
    assert consumed == len(reads)
    answer = (folder / 'answer.md').read_bytes()
    assert final == answer and digest(answer) == record['answer_sha256']
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--command', default=os.environ.get('VULKAN_SKILL_MODEL_CMD'))
    parser.add_argument('--model', default=os.environ.get('VULKAN_SKILL_MODEL_ID'))
    parser.add_argument('--parameters', default=os.environ.get('VULKAN_SKILL_MODEL_PARAMETERS', '{}'))
    parser.add_argument('--skill-root', type=Path, default=SKILL_REPO)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--require-live', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--max-rounds', type=int, default=12)
    args = parser.parse_args(argv)
    # Refuse to overwrite any earlier outputs, including failed runs.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {'schema': 1, 'layer': 'Live', 'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'running', 'baseline_sha': BASELINE_SHA, 'cases': [],
                'model_identity_source': 'wrapper-attested; not independently provider-verified'}
    manifest_path = args.output_dir / 'manifest.json'
    try:
        if not args.command:
            manifest.update(status='skipped', reason='No model command configured; no live inference performed')
            print('SKIPPED: no model command configured')
            return 2 if args.require_live else 0
        if not args.model:
            raise ValueError('--model must identify the exact provider model/version')
        parameters = json.loads(args.parameters)
        if not isinstance(parameters, dict):
            raise ValueError('--parameters must be a JSON object')
        sha = subprocess.check_output(['git', '-C', str(args.skill_root), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(args.skill_root), 'status', '--porcelain'], text=True)
        manifest.update(skill_sha=sha, skill_dirty=bool(dirty), model=args.model, parameters=parameters,
                        command_sha256=digest(args.command), adapter_executable=Path(shlex.split(args.command)[0]).name, max_rounds=args.max_rounds, timeout=args.timeout)
        for case in args.case or CASES:
            manifest['cases'].append(case)
            write_json(manifest_path, manifest)
            run_case(args.skill_root, args.command, args.model, parameters, case,
                     args.output_dir / case, args.max_rounds, args.timeout)
        end_sha = subprocess.check_output(['git', '-C', str(args.skill_root), 'rev-parse', 'HEAD'], text=True).strip()
        end_dirty = subprocess.check_output(['git', '-C', str(args.skill_root), 'status', '--porcelain'], text=True)
        manifest.update(skill_end_sha=end_sha, skill_end_dirty=bool(end_dirty))
        if end_sha != sha or end_dirty != dirty:
            raise RuntimeError('Skill checkout changed during live run; retained evidence is not a consistent release run')
        manifest['status'] = 'generated'  # Never equate generation with correctness.
        write_json(manifest_path, manifest)
        if args.check:
            env = dict(os.environ, VULKAN_LIVE_RUN_DIR=str(args.output_dir.resolve()))
            result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-m', 'live', str(BASE)], env=env, check=False)
            manifest['gate_exit_code'] = result.returncode
            manifest['status'] = 'gate_passed' if result.returncode == 0 else 'gate_failed'
            return result.returncode
        return 0
    except Exception as exc:
        manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        print(manifest['error'])
        return 1
    finally:
        manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_json(manifest_path, manifest)


if __name__ == '__main__':
    raise SystemExit(main())
