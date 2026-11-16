"""Authored CPU failure fixture, NOT a Vulkan driver or Live engineering run.

Models the fence-reset trap for E2E19-02. Acquire failure means no submission
will signal the reset fence. Production code must use its real frame owner.
"""
class Frame:
    def __init__(self): self.signaled=True;self.pending=False;self.acquired=False
    def wait(self):
        if not self.signaled: raise TimeoutError('no completion signal')
    def acquire(self,ok): self.acquired=ok;return ok
    def reset(self): self.signaled=False
    def submit(self):
        if not self.acquired: raise ValueError('no acquired output')
        self.pending=True
    def complete(self):
        if not self.pending: raise ValueError('no pending submit')
        self.signaled=True;self.pending=False;self.acquired=False

def broken_frame(frame,acquire_ok):
    frame.wait();frame.reset()
    if not frame.acquire(acquire_ok): return 'RECREATE'
    frame.submit();return 'SUBMITTED'

def fixed_frame(frame,acquire_ok):
    frame.wait()
    if not frame.acquire(acquire_ok): return 'RECREATE'
    frame.reset();frame.submit();return 'SUBMITTED'
