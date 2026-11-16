# Bounded timeline HOST contract

```sh
python checks19/run_timeline_contracts.py \
 --synchronization /path/to/frozen368/chapters/synchronization.adoc \
 --validusage /path/to/frozen309/validusage.json --out /fresh/output
```

This verifies exact normative source bytes and runs 14 fixed HOST controls. Raw
prose slices, conditional directives, 309 VUID coordinates and implementation
hashes remain auditable. It is not device execution, concurrent scheduling,
complete semaphore validation or full L1/L2 acceptance.

`host_signal` requires an ordinary enabled timeline, a caller-proven at-call
state, complete outstanding wait/signal inventory and serialized host signal
calls. A previously read counter alone cannot establish this state. Values are
exact uint64 without bool coercion or wraparound. A signal must exceed current,
be below every pending signal, and remain within maxTimelineSemaphoreValueDifference
of current and every outstanding wait/signal. Numeric order is not execution
order: each outstanding signal must independently happen after this host signal.
The model neither authenticates those proofs nor executes a signal.

`wait_condition` evaluates only the supplied snapshots: ANY means at least one
counter >= its target; ALL means every counter >= target. It predicts neither
VkResult nor timeout/deadlock. In particular wait-before-signal is not by itself
a deadlock. Snapshots can immediately become stale.

`retirement` does not derive destruction safety from successful waiting or a high
counter. It requires a complete caller-proven set of completed submitted
references, completed relevant host calls and no concurrent host access. Its result concerns only those obligations; other object-destruction
and concurrent-host requirements remain separate. A timeline value may represent
one completion point without retiring all outstanding uses.

The source map preserves physical raw sections, not expanded includes, outer
conditional applicability or dependency closure. Source368 and VUID309 are
separate cohorts. All controls are authored semantic fixtures, not production
bug evidence, physical GPU performance data or release acceptance.
