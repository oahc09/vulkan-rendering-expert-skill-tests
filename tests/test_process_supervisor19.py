"""CPU subprocess fixtures only: no GPU hang, Vulkan device loss or system mutation."""
import importlib.util,os,signal,subprocess,sys,time,threading
from pathlib import Path
import pytest
pytestmark=pytest.mark.host_unit
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('supervisor',ROOT/'checks19/process_supervisor19.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
def run(tmp_path,code,timeout=.4,cancel=None):
 return s.run_step([sys.executable,'-u','-c',code],tmp_path/'stdout',tmp_path/'stderr',timeout=timeout,total_deadline=time.monotonic()+10,cancellation=cancel or s.Cancellation(),grace=.15)
def gone(pid):
 try:os.kill(pid,0);return False
 except ProcessLookupError:return True
CHILD="import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)"
def tree(parent_exit=False):
 return f"import subprocess,sys,time,signal;p=subprocess.Popen([sys.executable,'-c',{CHILD!r}]);print(p.pid,flush=True);"+('time.sleep(.15)' if parent_exit else 'signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)')
def test_success_and_logs(tmp_path):
 r=run(tmp_path,"print('success')",timeout=2)
 assert r['returncode']==0 and r['group_cleanup']['group_gone'] and not r['timed_out']
 assert (tmp_path/'stdout').read_text().strip()=='success'
def test_timeout_reaps_parent_and_descendant(tmp_path):
 r=run(tmp_path,tree());pid=int((tmp_path/'stdout').read_text())
 assert r['timed_out'] and r['group_cleanup']['kill_sent'] and r['group_cleanup']['group_gone']
 assert gone(r['pid']) and gone(pid)
def test_parent_exits_first_descendant_still_reaped(tmp_path):
 r=run(tmp_path,tree(True),timeout=2);pid=int((tmp_path/'stdout').read_text())
 assert r['returncode']==0 and r['unexpected_descendants'] and r['group_cleanup']['group_gone'] and gone(pid)
def test_cancel_file_reaps_group(tmp_path):
 cancel=tmp_path/'cancel';timer=threading.Timer(.3,lambda:cancel.touch());timer.start()
 try:r=run(tmp_path,tree(),timeout=3,cancel=s.Cancellation(cancel))
 finally:timer.cancel();timer.join()
 assert r['cancelled'] and r['group_cleanup']['group_gone'] and gone(int((tmp_path/'stdout').read_text()))
def test_unrelated_sentinel_survives(tmp_path):
 sentinel=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
 try:
  r=run(tmp_path,tree());assert r['timed_out'] and sentinel.poll() is None
 finally:sentinel.terminate();sentinel.wait(timeout=3)
def test_launch_failure_retains_error(tmp_path):
 r=s.run_step(['/not-a-real-command'],tmp_path/'out',tmp_path/'err',timeout=1,total_deadline=time.monotonic()+2,cancellation=s.Cancellation())
 assert r['returncode'] is None and r['launch_error']=='FileNotFoundError' and (tmp_path/'err').read_bytes()
def test_total_budget_reaps_group(tmp_path):
 r=s.run_step([sys.executable,'-c',tree()],tmp_path/'out',tmp_path/'err',timeout=5,total_deadline=time.monotonic()+.3,cancellation=s.Cancellation(),grace=.1)
 assert r['timed_out'] and r['budget_exhausted'] and r['group_cleanup']['group_gone']
def test_pre_cancel_never_launches(tmp_path):
 flag=tmp_path/'cancel';flag.touch()
 with pytest.raises(s.Cancelled):run(tmp_path,"raise SystemExit(0)",cancel=s.Cancellation(flag))
 assert not (tmp_path/'stdout').exists()
def test_signal_handler_converts_sigint_and_restores(tmp_path):
 cancel=s.Cancellation();before=signal.getsignal(signal.SIGINT);cancel.install();timer=threading.Timer(.25,lambda:os.kill(os.getpid(),signal.SIGINT));timer.start()
 try:r=run(tmp_path,tree(),timeout=3,cancel=cancel)
 finally:timer.cancel();timer.join();cancel.restore()
 assert r['cancelled'] and r['group_cleanup']['group_gone'] and signal.getsignal(signal.SIGINT)==before
def test_signals_only_before_leader_reaped(monkeypatch,tmp_path):
 original_popen=s.subprocess.Popen;original_kill=s.os.killpg;owned=[];signals=[]
 def launch(*args,**kw):
  proc=original_popen(*args,**kw);owned.append(proc);return proc
 def kill(pgid,sig):
  assert owned and pgid==owned[0].pid and owned[0].returncode is None
  # WNOWAIT still observes this same owned unreaped leader.
  s.os.waitid(s.os.P_PID,pgid,s.os.WEXITED|s.os.WNOHANG|s.os.WNOWAIT)
  signals.append(sig);return original_kill(pgid,sig)
 monkeypatch.setattr(s.subprocess,'Popen',launch);monkeypatch.setattr(s.os,'killpg',kill)
 r=run(tmp_path,"print('done')",timeout=2)
 assert r['returncode']==0 and signals==[signal.SIGTERM,signal.SIGKILL]
def test_subreaper_restored_on_cleanup_exception(monkeypatch,tmp_path):
 # The fake cleanup fails only after actual cleanup, so this test leaks no process.
 original=s.terminate_group;restore=[];sub=s.subreaper
 def track(value):restore.append(value);return sub(value)
 def fail(proc,grace):original(proc,grace);raise OSError('injected cleanup reporting failure')
 monkeypatch.setattr(s,'subreaper',track);monkeypatch.setattr(s,'terminate_group',fail)
 with pytest.raises(OSError):run(tmp_path,"print('done')",timeout=2)
 assert restore[0] is True and restore[-1] in (0,1) and len(restore)==2
