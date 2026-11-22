# Physical-storage device-address pointer chain

Bounded address-support family, not an implementation of unavailable VK16 optical/tensor/data-graph/cooperative functionality. The included actual capability inventory queries Video codecs/queues and special extension names, including KHR/NV copy_memory_indirect. Missing extensions are UNSUPPORTED, never emulated or declared passed. Subgroup belongs to separate VK08 scope.

The device actually queries/enables Vulkan1.2 bufferDeviceAddress and shaderInt64. Three separately allocated coherent buffers contain input(68uint), output(68uint), and pointer table(2uint64). Each buffer is bound with DEVICE_ADDRESS allocation flag and SHADER_DEVICE_ADDRESS usage. The table has actual source/output addresses at offsets0/8; its address is pushed to compute. Reference bases are16-aligned; generated SPIR-V pointer-field loads use Aligned16/8 respectively and indexed uint loads/stores use Aligned4, not16 per element. Runner checks named layout/instruction presence; operand-to-pointer data flow is manually reviewed in this source/SPV cohort, not a complete automated reflector or formal proof. Actual requirements alignment and bind offset0 are recorded and verified independently of shader reference alignment.

64invocations (8local×8groups) traverse the physical pointer table and compute output[i]=input[i]*3+i. All64 outputs are independently compared to CPU pattern17+7*i; source and4word output guard plus both table entries must remain unchanged. Entire source/output are emitted after real host-write→shader read/write and shader-write→host-read dependencies and a completed fence. All allocation generations remain live through dispatch and retirement. No out-of-bounds/stale pointer is dispatched; descriptor robustness does not protect physical pointers.

Safe missing-usage control calls vkGetBufferDeviceAddress for a valid bound allocation with STORAGE but no SHADER_DEVICE_ADDRESS. Exact02601 callback-abort returns zero; address is not pushed/submitted. Wrong-output genuinely compares against per-element expected+1 and exits6 with clean VVL. These are authored fixtures, not external production failures.

On DeviceWaitIdle failure cleanup terminates nonzero without destroying possibly pending Vulkan objects. This branch is source-audited, not an injected GPU-fault/recovery test.

Set trusted CPU ICD/Validation env variables and run:
```
python -O cases19/device_address/run.py --tools TOOL_BIN --include HEADERS --loader LOADER --validusage VALIDUSAGE --output FRESH_DIRECTORY
```
Exact validusage1.4.30902601 entry checked against full snapshot. All code/SPV/disassembly/tool/report hashes retained. Standalone CPU ICD cohort, not physical hardware, capture/replay, sparse memory, special extension execution, performance or complete VK16 acceptance.
