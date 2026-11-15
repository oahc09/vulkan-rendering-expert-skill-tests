"""Candidate identity/packaging only; never a final capability acceptance seal."""
import argparse, hashlib, json, pathlib, subprocess
p=argparse.ArgumentParser(); p.add_argument('--skill'); p.add_argument('--resolve',action='store_true')
a=p.parse_args(); root=pathlib.Path(__file__).resolve().parents[1]
c=json.loads((root/'coverage/v1.0.19/pair.json').read_text())
if a.resolve:
 print(c['skill_sha']); raise SystemExit
skill=pathlib.Path(a.skill).resolve()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=skill,text=True).strip()==c['skill_sha']
assert hashlib.sha256((root/'docs/v1.0.19-original-plan.md').read_bytes()).hexdigest()==c['plan_sha256']
assert 'version: 1.0.19' in (skill/'SKILL.md').read_text()
assert 'candidate-blocked' in (skill/'SKILL.md').read_text()
assert c['release_status']=='BLOCKED'
print('PASS exact candidate identity; final acceptance remains BLOCKED')
