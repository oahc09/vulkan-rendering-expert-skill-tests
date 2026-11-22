# OPAQUE_FD memory-object ownership lifecycle (no data path)
Original authored fixture; not an external-production defect. Two distinct VkInstance/VkDevice objects in one process, each enumerating exactly one CPU physical device with identical deviceUUID/driverUUID. No queues are submitted, memory mapped, payload read or external synchronization claimed.

```
python -O cases19/external_memory/run.py --include HEADERS --loader LOADER --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```
Actual extension discovery and OPAQUE_FD transfer-buffer query require import/export and compatible handle bits. Both exclusive buffers have identical1024-byte create parameters and queried requirements2/dedicated requirements. Common memoryTypeBits select the same exporting/importing type. Both allocations explicitly dedicated to their respective buffers, with identical allocationSize equal to queried requirements. Runner sends actual records into external_memory19.admit and verifies bind success.

Two successful exports create distinct valid app-owned FDs while both remain open. The first is transferred through successful import; immediately afterward the app sets its tracking variable to-1 and never checks or closes the consumed descriptor. The second remains app-owned and is explicitly closed once. Import failure leaves ownership with app, cleanup closes remaining app-owned descriptors. Ownership is not inferred from numeric reuse after transfer.

`properties` control calls vkGetMemoryFdPropertiesKHR with valid app-owned OPAQUE_FD, which is expressly forbidden by00674. Validation callback aborts, return VK_ERROR_VALIDATION_FAILED_EXT and exact phase/VUID are checked; FD remains app-owned and is subsequently closed. This query does not consume the FD. Good mode has no errors. Import buffer stays allocated while exporter buffer/memory/device/instance are destroyed, then importer is cleanly destroyed. This is legal object lifecycle evidence, **not proof of payload contents or cross-device visibility**.

Current CPU cohort exposes memory_fd, but no semaphore_fd/fence_fd extension. Cross-device GPU data/synchronization path is NOT_RUN. A fence on deviceA is not silently treated as sufficient memory synchronization for deviceB. No physical hardware, cross-process/API, external memory image/dma_buf/Win32 or full VK17 acceptance.

Normative excerpts are exact entries from schema2 validusage1.4.309 with original source SHA, version, owner and condition; runner checks them against the complete input file. Source/runner/rules/normative/binary/loader and ICD/layer manifest hashes, actual queries and raw logs are recorded. A local hash is provenance/integrity, not hardware attestation. Unsupported scope/API failures/timeouts cannot generate successful summary.
