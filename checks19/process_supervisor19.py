"""Linux scoped subprocess-group supervision; never targets unrelated processes.
No GPU hang/device-loss claim. Descendants must remain in the launched session/group.
"""
import ctypes
import os
import signal
import subprocess
import time

class Cancelled(RuntimeError):pass
class BudgetExceeded(RuntimeError):pass

class Cancellation:
    def __init__(self,path=None):self.path=path;self.signal_number=None;self.previous={}
    def requested(self):return self.signal_number is not None or (self.path is not None and self.path.exists())
    def install(self):
        for s in (signal.SIGINT,signal.SIGTERM):
            self.previous[s]=signal.getsignal(s);signal.signal(s,self._handler)
    def _handler(self,signum,frame):self.signal_number=signum
    def restore(self):
        for s,h in self.previous.items():signal.signal(s,h)
    def check(self,deadline):
        if self.requested():raise Cancelled('explicit cancel-file or termination signal')
        if time.monotonic()>=deadline:raise BudgetExceeded('total delivery budget exhausted')

def leader_exited(proc):
    # Keep the direct child unreaped until teardown: its PID cannot be reused.
    status=os.waitid(os.P_PID,proc.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
    return status is not None and status.si_pid==proc.pid

def subreaper(enable):
    libc=ctypes.CDLL(None,use_errno=True)
    previous=ctypes.c_int()
    if libc.prctl(37,ctypes.byref(previous),0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_GET_CHILD_SUBREAPER')
    if libc.prctl(36,int(enable),0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')
    return previous.value

def terminate_group(proc,grace):
    """Signal only while unreaped leader reserves the PGID; never signal after wait.

    This sandbox lacks /proc task children. No global process scan is needed:
    after final KILL, reap the direct child then only adopted group children.
    """
    record={'pgid':proc.pid,'term_sent':False,'kill_sent':False,'reaped_descendants':[]}
    try:leader_exited(proc)
    except ChildProcessError:
        record.update(group_gone=False,ownership_lost=True);return record
    try:os.killpg(proc.pid,signal.SIGTERM);record['term_sent']=True
    except ProcessLookupError:pass
    deadline=time.monotonic()+grace
    while time.monotonic()<deadline:time.sleep(min(.02,max(0,deadline-time.monotonic())))
    # Leader has never been reaped, even if zombie: its PID cannot be recycled.
    try:os.killpg(proc.pid,signal.SIGKILL);record['kill_sent']=True
    except ProcessLookupError:pass
    # All signaling is now permanently over. Numeric PGID is only used for our
    # own child reaping, not for probing/signaling a potentially reused group.
    try:proc.wait(timeout=max(1,grace))
    except subprocess.TimeoutExpired:
        record.update(group_gone=False,direct_child_unreaped=True);return record
    deadline=time.monotonic()+max(1,grace)
    while time.monotonic()<deadline:
        try:pid,_=os.waitpid(-proc.pid,os.WNOHANG)
        except ChildProcessError:
            record['group_gone']=True;return record
        if pid:record['reaped_descendants'].append(pid)
        else:time.sleep(.02)
    record['group_gone']=False;return record

def run_step(argv,stdout_path,stderr_path,*,timeout,total_deadline,cancellation,grace=1.0):
    """Write logs directly; return actual exit and teardown record on all outcomes."""
    cancellation.check(total_deadline)
    result={'returncode':None,'timed_out':False,'cancelled':False,'budget_exhausted':False,'group_cleanup':None}
    previous=subreaper(True);proc=None;cleaned=False
    try:
        with stdout_path.open('wb') as out,stderr_path.open('wb') as err:
            try:proc=subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True)
            except OSError as e:
                result['launch_error']=type(e).__name__;err.write(str(e).encode());return result
            result['pid']=proc.pid;result['pgid']=proc.pid
            deadline=min(time.monotonic()+timeout,total_deadline)
            while True:
                if cancellation.requested():result['cancelled']=True;break
                if time.monotonic()>=deadline:
                    result['timed_out']=True;result['budget_exhausted']=time.monotonic()>=total_deadline;break
                if leader_exited(proc):break
                time.sleep(.025)
            result['group_cleanup']=terminate_group(proc,grace);cleaned=True
            result['unexpected_descendants']=bool(result['group_cleanup']['reaped_descendants']) and not result['cancelled'] and not result['timed_out']
            result['returncode']=proc.returncode
        return result
    finally:
        # Also covers Python exceptions/KeyboardInterrupt outside the installed handler.
        try:
            if proc is not None and not cleaned and proc.returncode is None:terminate_group(proc,grace)
        finally:
            subreaper(previous)
