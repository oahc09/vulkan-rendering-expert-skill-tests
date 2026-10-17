"""Harness unit tests use explicit mocks, never model-behavior evidence."""
import json
import subprocess
from pathlib import Path

import pytest
import run_live_model_behavior as runner


def test_section_selection_is_bounded_and_ignores_code():
    text = '# A\nintro\n## Wanted\nbody\n### Child\nchild\n```\n## Not a heading\n```\n## Other\nend\n'
    selected, start, end = runner.select_section(text, 'Wanted')
    assert 'Child' in selected and 'Other' not in selected
    assert (start, end) == (3, 9)
    with pytest.raises(ValueError):
        runner.select_section(text, 'missing')
    with pytest.raises(ValueError):
        runner.select_section('## Same\na\n## Same\nb\n', 'Same')


def test_read_refuses_escape_and_symlinks(tmp_path):
    root = tmp_path / 'skill'; root.mkdir()
    (tmp_path / 'secret.md').write_text('not context')
    (root / 'link.md').symlink_to(tmp_path / 'secret.md')
    for path in ['../secret.md', 'link.md', '/etc/passwd', 'missing.md']:
        with pytest.raises(ValueError):
            runner.read_context(root, path)


def test_no_model_records_skip_without_responses(tmp_path, monkeypatch):
    monkeypatch.delenv('VULKAN_SKILL_MODEL_CMD', raising=False)
    out = tmp_path / 'run'
    assert runner.main(['--output-dir', str(out)]) == 0
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['status'] == 'skipped'
    assert not list(out.rglob('answer.md'))
    assert runner.main(['--output-dir', str(tmp_path/'strict'), '--require-live']) == 2
    with pytest.raises(FileExistsError):
        runner.main(['--output-dir', str(out)])


def setup_case(tmp_path):
    root = tmp_path / 'skill'; root.mkdir()
    (root / 'SKILL.md').write_text('# Skill\nRead rules as needed.\n')
    (root / 'rules.md').write_text('## Relevant\nneeded\n## Irrelevant\nnot needed\n')
    return root


def test_progressive_reads_and_exact_transcript_hashes(tmp_path, monkeypatch):
    root = setup_case(tmp_path)
    replies = [{'read': [{'path': 'rules.md', 'section': 'Relevant'}]}, {'answer': 'MOCK UNIT TEST ONLY'}]
    seen = []
    def fake(command, prompt, timeout):
        seen.append(prompt)
        output = json.dumps({'model': 'unit-mock', 'parameters': {'temperature': 0}, 'usage': {'input_tokens': 100, 'output_tokens': 20}, 'response': replies.pop(0)}).encode()
        return subprocess.CompletedProcess(command, 0, output, b'')
    monkeypatch.setattr(runner, 'run_model', fake)
    out = tmp_path / 'case'
    record = runner.run_case(root, 'unused', 'unit-mock', {'temperature': 0}, runner.CASES[0], out)
    assert '## Relevant' not in seen[0] and '## Relevant' in seen[1]
    assert 'not needed' not in seen[1]
    assert record['reads'][1]['section'] == 'Relevant'
    assert record['status'] == 'generated'
    manifest = {'model': 'unit-mock', 'parameters': {'temperature': 0}}
    runner.audit_case(out, manifest)
    original = (out / 'read-01.txt').read_bytes()
    (out / 'read-01.txt').write_bytes(b'tampered')
    with pytest.raises(AssertionError):
        runner.audit_case(out, manifest)
    (out / 'read-01.txt').write_bytes(original)
    for step in record['rounds']:
        assert runner.digest((out / step['input_file']).read_bytes()) == step['input_sha256']
        assert runner.digest((out / step['output_file']).read_bytes()) == step['output_sha256']


@pytest.mark.parametrize('failure', ['nonzero', 'empty', 'wrong-model', 'duplicate', 'timeout', 'max-rounds', 'missing-usage', 'wrong-parameters', 'empty-answer', 'malformed-json'])
def test_failures_are_retained_not_rewritten(tmp_path, monkeypatch, failure):
    root = setup_case(tmp_path)
    def fake(command, prompt, timeout):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, timeout, output=b'partial unit output', stderr=b'unit timeout')
        if failure in ('nonzero', 'empty'):
            return subprocess.CompletedProcess(command, 3 if failure == 'nonzero' else 0, b'', b'unit failure')
        response = {'read': [{'path': 'SKILL.md'}]} if failure == 'duplicate' else {'read': [{'path': 'rules.md'}]}
        envelope = {'model': 'wrong' if failure == 'wrong-model' else 'unit-mock', 'parameters': {}, 'usage': {'input_tokens': 100, 'output_tokens': 20}, 'response': response}
        if failure == 'missing-usage':
            envelope.pop('usage')
        if failure == 'wrong-parameters':
            envelope['parameters'] = {'temperature': 1}
        if failure == 'empty-answer':
            envelope['response'] = {'answer': ''}
        raw = b'not json' if failure == 'malformed-json' else json.dumps(envelope).encode()
        return subprocess.CompletedProcess(command, 0, raw, b'')
    monkeypatch.setattr(runner, 'run_model', fake)
    out = tmp_path / 'case'
    with pytest.raises((ValueError, RuntimeError, subprocess.TimeoutExpired)):
        runner.run_case(root, 'unused', 'unit-mock', {}, runner.CASES[0], out, max_rounds=1)
    assert json.loads((out / 'record.json').read_text())['status'] == 'failed'
    assert (out / '00.input.txt').is_file()
    assert not (out / 'answer.md').exists()
    if failure == 'timeout':
        assert (out / '00.output.partial').read_bytes() == b'partial unit output'
    with pytest.raises(FileExistsError):
        runner.run_case(root, 'unused', 'unit-mock', {}, runner.CASES[0], out)


def test_stable_anchor_and_path_anchor_reads(tmp_path):
    (tmp_path / 'entry.md').write_text('<a id="route-api"></a>\n## API route\nneeded\n## Other\nnot needed\n')
    selected, record = runner.read_context(tmp_path, 'entry.md#route-api')
    assert 'needed' in selected and 'Other' not in selected
    assert record['section'] == '#route-api'
    same, _ = runner.read_context(tmp_path, 'entry.md', '#route-api')
    assert same == selected
    with pytest.raises(ValueError):
        runner.read_context(tmp_path, 'entry.md#route-api', 'API route')
