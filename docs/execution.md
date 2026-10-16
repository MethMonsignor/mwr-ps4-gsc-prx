[Repository](../README.md) · [Complete reference](reference.md#5-load-link-and-execution-sequence)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## 5. Load, link and execution sequence

```mermaid
sequenceDiagram
    participant E as Engine lifecycle
    participant P as PRX hooks
    participant V as Native loader and VM
    participant G as Custom GSC
    E->>P: Zone-load detour
    P->>V: Original zone load, then checked allocation
    E->>P: Selected stock script load
    P->>V: Original stock load
    V-->>P: Stock result; linker context still live
    P->>V: Load private PRIVATE_SCRIPT_NAME
    V->>P: ScriptFile lookup and default check
    P-->>V: Private descriptor and non-default result
    V-->>P: Linked script object
    P->>V: Resolve main token 0x267
    E->>P: Stock start-gametype execution
    P->>V: Execute original callback first
    P->>V: Execute custom handle on level object
    V->>G: main()
    G-->>P: API and fresh epoch DVARs
    P->>V: Release custom returned object reference
```

### A. PRX initialization

The functional plugin entry is `plugin_load()`. The exported `module_start()` and `module_stop()` in this project simply return zero. `plugin_load()` calls `initialize_loader()`, which prepares the GSC directory and reads the configuration/payload. The native initialization path discovers the engine base and eventually calls `install_loader_hooks(base)` from `try_install_renderer()`.

Configuration shape; substitute the configured private script name:

```ini
mode=standalone
target=<private-script-name>
```

Runtime files; `SCRIPT_DIRECTORY` represents the configured directory:

| Path | Purpose |
|---|---|
| `SCRIPT_DIRECTORY/config.ini` | Mode and exact private script name |
| `SCRIPT_DIRECTORY/payload.gscbin` | Compiled, packaged payload |
| `SCRIPT_DIRECTORY/scriptfiles.log` | Saved observed ScriptFile names |
| `SCRIPT_DIRECTORY/arena_diagnostic.txt` | Saved loader/arena snapshot |
| `SCRIPT_DIRECTORY/native_session.txt` | Separate native session/startup report |

### B. Reserve engine-owned bytecode storage

`zone_load_hook()` invokes the original routine first. On return, `arena_reserve()` considers a standalone candidate only when its bounded zone name starts with `mp_` and its block descriptor contains a nonempty script block. It verifies the allocator's current pool, owner, cursor, capacity and stock block before requesting a 32 KiB reservation.

It records the allocation address and ownership metadata for later checks. A merely successful `malloc()` would not satisfy this requirement; the VM uses its own program-base/range model.

### C. Use the live linking window

The full-load boundary is the call at `0x0024568C`, with return address `B + 0x00245691` and depth zero. Before delegating this stock call, `load_script_at()` invalidates the old standalone handle and acknowledgement state.

After the stock call returns, it requires a nonzero stock result, nonnull caller scratch, the expected native scripting thread, the active loading flag and all three linking roots. This occurs **inside the outer MP initialization routine**, before its caller scratch and linking structures are released.

The loader then reads a possible payload update within this window. It copies **pristine, unlinked** bytecode from the retained file image into the owned engine arena and points `scriptAsset.bytecode` there. Relinking bytes that already contain runtime string/field fixups is deliberately avoided.

### D. Expose the synthetic asset only for the private load

Before making the native load call, the PRX records the current thread and sets `supplyingPrivateAsset`. During that call, the asset/default hooks recognize only:

1. ScriptFile asset type **48 / `0x30`**.
2. Exact match with the configured private-name string (`PRIVATE_SCRIPT_NAME`).
3. A currently installed, active supply window.
4. The same native thread as the explicit load.
5. A ready, unreleased engine arena.

For that request, `asset_lookup_hook()` returns `&scriptAsset`; `asset_default_hook()` returns zero. Both are necessary: the stock loader calls asset lookup at `0x007DAEF0` and then the default check at `0x007DAF00`. A descriptor alone would still leave the private name subject to the stock missing/default logic.

All other names, types and threads follow the original DB routines. The implementation does not insert this private asset into the global DB hash tables or replace a map's main function in standalone mode. The descriptor resides in PRX storage; its exposure is temporary, while its storage lifetime is deliberately long.

### E. Resolve and validate `main`

After the private native load returns successfully, `get_function_handle(PRIVATE_SCRIPT_NAME, 0x267)` resolves the first export. `standalone_range_failure()` checks both the code allocation and the entry:

- The payload fits the current reserved capacity.
- Its code span lies in the current VM program range.
- The handle is nonzero, positive within the implementation's signed limit, and less than the program-range length.
- `programBase + handle` points inside this payload's actual code span.
- The arena's recorded owner and committed span remain live.

The handle and loaded flag are published only after these checks. The original stock load result is returned to the engine unchanged.

### F. Execute after stock gametype startup

The native executor detour sees many calls, but the custom launch branch only accepts the return address `B + 0x00679CB3` and zero arguments. It first runs the original start-gametype callback and preserves its returned reference.

After validating current context, it prepares a fresh expected acknowledgement epoch, invokes the custom main through the executor's original-function stub with the same **level object** and zero arguments, then releases the custom returned reference through `remove_object_reference()`. It returns the original stock reference to the stock caller.

The precache flag is still set at this point. The payload's `main()` precaches the white shader and weapon catalogue before starting its menu thread. Calling the entry after this window would not preserve that requirement.

### G. Continue in the game's VM

The GSC creates its own thread with `thread menu_boot()`, waits with normal VM instructions, creates HUD entities through native builtins, and reads game actions. `level.menu_running` prevents duplicate startup calls from creating duplicate menu loops/HUDs. Duplicate entry calls acknowledge the new epoch and return.

The PRX has no separate GSC interpreter and no native worker that repeatedly calls script instructions. Releasing the external returned reference does not cancel the VM's wait/scheduling ownership. A nonzero execution result is still weaker evidence than a fresh GSC-written acknowledgement and an observed menu.
