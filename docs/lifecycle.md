[Repository](../README.md) · [Complete reference](reference.md#9-restarts-updates-disarming-and-unloading)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## 9. Restarts, updates, disarming and unloading

| Event | Existing behavior |
|---|---|
| Full script load | Invalidates old handle/acknowledgements, reads candidate package, copies pristine code and links again within the selected window. |
| Retained-code quick restart | Reuses the checked linked handle and arena; starts the menu at the stock startup boundary and expects a new acknowledgement. Does not apply a pending disk update. |
| Owning zone released | Clears readiness/code address/handle/acknowledgements before original release; resets the reservation-attempt latch so a later eligible map can allocate. |
| Unrelated zone/owner released | Leaves the current reservation's ownership state alone. |
| Valid changed package at full load | Publishes a new cached generation, retaining previously exposed source bytes. |
| Identical package | Reuses the cached generation without growing retirement history. |
| Invalid, missing or incomplete update | Keeps an existing validated in-memory package. If none exists, waits for a valid package at a later full load. |
| Retired buffers would exceed 8 MiB | Refuses the changed candidate and keeps the cached package; process restart clears retention history. |
| `Check GSC Update` | Compatibility preview only. Does not change active code, handles or running threads. |
| `Disarm Future Starts` | Sets mode off for future custom starts. An already-running script is not terminated. |
| Unload request with arena/standalone hooks installed | `can_unload()` refuses unloading. Its rule is stricter than just checking whether a payload has launched. |

Compatible source edits must be compiled and packaged. After installation of a matching PRX, the runtime update file is `payload.gscbin`; copying raw `.gsc` text into its place will not work. Transfer completion must precede the next full script load.

There is no automatic rollback after an accepted payload encounters a runtime VM error, and no disk fallback copy is created by this loader. The fallback described above is the last validated package retained **in process memory**. A fatal engine error or nonlocal error unwind can bypass ordinary hook cleanup; the current code does not intercept those paths.
