# Mapped memory: discovery before claims

Original bounded experiment, not an external production defect. `run.py` builds
`probe.c`, starts four isolated processes and checks exact diagnostics, exit
codes, queried device/type records, and actual layer metadata against its manifest.
Only CPU devices are in this experiment's scope. All enumerated physical devices'
memory types and buffer compatibility bits are logged before selecting memory.

`visibility` requires a compatible HOST_VISIBLE type without HOST_COHERENT. When
available, it writes a host pattern, flushes, submits buffer copy and a transfer to
host-read barrier, waits its fence, invalidates the mapped readback allocation and
checks the pattern. When unavailable, its outcome is **UNAVAILABLE_NOT_RUN**. That
compiled branch is not promoted to runtime validated by other tests.

`good`, `offset` and `size` are separate API-boundary checks on compatible
host-visible memory (which can be coherent). They map [atom, 2*atom), then flush
respectively that range, [0,atom), and [atom,3*atom). Both negative cases are mapped
range containment VUID-VkMappedMemoryRange-size-00685, **not** atom misalignment
negative controls. The validation callback aborts invalid calls. A successful
flush on coherent memory does not demonstrate noncoherent visibility, and these
three modes do not perform GPU readback. No SyncVal/GPU-AV or hardware qualification
is claimed. Cleanup errors and process timeouts cannot produce a successful run.

Run with the actual CPU ICD and validation layer environment configured:

```sh
python -O cases19/mapped_memory/run.py --include "$VULKAN_INCLUDE" \
  --loader "$VULKAN_LOADER" --output "$FRESH_OUTPUT_DIRECTORY"
```

Outputs include raw stdout/stderr, source/runner/binary/loader/manifest hashes,
compiler identity, runtime layer version, every memory type and selected device
index/type/flags. Existing output directories are rejected to avoid stale evidence.
