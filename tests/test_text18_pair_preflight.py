"""Executable negative tests for pairing, not release acceptance."""
import json
import subprocess
import pytest
from text18_pair_preflight import inspect_pair


def cmd(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def commit(root, name):
    (root / name).write_text(name)
    cmd(root, 'add', '.')
    cmd(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', name)
    return cmd(root, 'rev-parse', 'HEAD')


@pytest.fixture
def pair(tmp_path):
    skill, tests = tmp_path/'skill', tmp_path/'tests'
    for root in (skill, tests):
        root.mkdir(); cmd(root, 'init', '-q')
    s = commit(skill, 'skill')
    main = commit(tests, 'main')
    base = commit(tests, 'base')
    c = {'skill_sha': s, 'tests_base_sha': base, 'unclosed': ['CORE17', 'target hardware']}
    (tests/'text18-candidate-contract.json').write_text(json.dumps(c))
    commit(tests, 'candidate')
    return skill, tests, main


def test_clean_stacked_pair_is_not_release(pair):
    s,t,m=pair; r=inspect_pair(s,t,tests_main=m)
    assert r['pair_status']=='PASS' and r['stacked_base_not_in_main']
    assert r['release_status']=='BLOCKED'


def test_base_in_main_still_not_release(pair):
    s,t,_=pair; r=inspect_pair(s,t,tests_main=cmd(t,'rev-parse','HEAD'))
    assert not r['stacked_base_not_in_main'] and r['release_status']=='BLOCKED'


def test_wrong_skill_rejected(pair):
    s,t,m=pair; commit(s,'wrong')
    assert 'SKILL_SHA_MISMATCH' in inspect_pair(s,t,tests_main=m)['errors']


def test_dirty_pair_rejected(pair):
    s,t,m=pair; (s/'dirty').write_text('not committed')
    assert 'DIRTY_CHECKOUT' in inspect_pair(s,t,tests_main=m)['errors']


def test_missing_history_not_treated_as_stacked(pair):
    s,t,_=pair
    with pytest.raises(subprocess.CalledProcessError): inspect_pair(s,t,tests_main='1'*40)


def test_mutable_ref_rejected(pair):
    s,t,_=pair
    with pytest.raises(ValueError): inspect_pair(s,t,tests_main='origin/main')


def test_unrelated_base_rejected(pair):
    s,t,m=pair
    original=cmd(t,'rev-parse','HEAD')
    cmd(t,'checkout','-q','--orphan','unrelated')
    other=commit(t,'unrelated')
    cmd(t,'checkout','-q',original)
    path=t/'text18-candidate-contract.json'
    c=json.loads(path.read_text()); c['tests_base_sha']=other
    path.write_text(json.dumps(c)); commit(t,'bad-base-contract')
    assert 'BASE_NOT_ANCESTOR' in inspect_pair(s,t,tests_main=m)['errors']


def test_config_cannot_hide_untracked_files(pair):
    s,t,m=pair; cmd(s,'config','status.showUntrackedFiles','no')
    (s/'hidden').write_text('untracked')
    assert 'DIRTY_CHECKOUT' in inspect_pair(s,t,tests_main=m)['errors']


@pytest.mark.parametrize('flag',['--assume-unchanged','--skip-worktree'])
def test_index_flags_cannot_claim_exact_pair(pair,flag):
    s,t,m=pair; cmd(s,'update-index',flag,'skill')
    (s/'skill').write_text('changed bytes')
    assert 'HIDDEN_INDEX_FLAGS' in inspect_pair(s,t,tests_main=m)['errors']


def test_shallow_history_is_unverified(pair,tmp_path):
    s,t,m=pair
    shallow=tmp_path/'shallow'
    subprocess.check_call(['git','clone','-q','--depth=1',t.as_uri(),str(shallow)])
    with pytest.raises(ValueError,match='shallow'):
        inspect_pair(s,shallow,tests_main=m)
