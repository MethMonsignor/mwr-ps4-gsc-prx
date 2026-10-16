[Repository](../README.md) · [Complete reference](reference.md#6-memory-ownership-and-the-script-arena)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## 6. Memory ownership and the script arena

### Why ordinary heap bytecode was insufficient

The engine reads `ScriptFile.bytecode` directly. At `0x007DA956`, handle resolution subtracts the current program base. At `0x007DA95D`–`0x007DA960`, an offset outside the program range becomes zero. Conversely, the executor adds the program base at `0x007E28E7`.

Thus, a valid-looking asset header and an increasing lookup counter do not prove executable code is reachable. The current design asks the engine allocator for memory within its existing script-pool arrangement, and verifies both pool ownership and VM range.

### Reservation checks

`arena_reserve()` reproduces the selector used for physical type 0 / allocation type 5, allowing only pool index 0 or 1. It checks a count from 1 through 32, the current owner and final slot owner, a 1 MiB pool region, ordered start/cursor/committed pointers, and a nonempty real stock script block.

The expected return address is `align_up(cursor, 16)`. Standalone mode requests **32,768 bytes**. The allocation must fit within the pool region, including the allocator's 64 KiB commitment boundary. The stock script block must end no later than the expected new allocation. After the call, the returned address, owner, cursor and committed end are read back.

The code reserves within existing engine bounds; it does not patch the VM's 2 MiB range, enlarge the pool, or replace the system allocator. The 2 MiB program range and 1 MiB per-pool region are different concepts, neither of which equals the available space for this payload.

### Ownership by allocation type

| Storage | Owner | Lifetime policy |
|---|---|---|
| `scriptAsset` descriptor and target name | PRX static storage | Must remain resident while engine references may exist. |
| Current package bytes / compressed metadata | PRX heap | Kept as the validated source image; pristine code is copied from it before each full link. |
| Retired, previously exposed packages | PRX heap | Retained until process exit; cumulative retirement cap 8 MiB. |
| Live linked bytecode | Engine zone allocator | Invalidated by the matching pool-owner release; never PRX-freed. |
| Caller scratch and linking roots | Stock engine loader | Borrowed only inside the selected native load window. |
| GSC threads, VM objects and HUD entities | Engine VM / game | Normal VM scheduling and script cleanup; external launch reference released separately. |

`payloadPinned` is set before exposing the custom asset, not only after a successful launch. It intentionally survives context invalidation. A link failure does not establish that every engine reference was discarded.

The shared state uses a small atomic lock. Long operations such as the engine allocator, native linking/execution and file reads run outside that lock with state gates such as `loaderBusy` and `updateWindowOpen`. This reduces reentry/deadlock risk without pretending that engine fatal-error unwinding is handled.
