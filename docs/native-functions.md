[Repository](../README.md) · [Complete reference](reference.md#2-native-functions-and-callable-signatures)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## 2. Native functions and callable signatures

### Calling convention

The PRX build targets `x86_64-pc-freebsd12-elf`. The relevant calls follow the x86-64 System V integer/pointer register convention: arguments 1–6 use RDI, RSI, RDX, RCX, R8 and R9; 32-bit integer arguments use their low halves. Pointers return in RAX, 32-bit scalar results in EAX, and the script-thread reference is consumed from AX. Floating-point values use XMM registers where applicable. These are not Windows x64 RCX/RDX/R8/R9 prototypes.

The declarations below reproduce the **contracts used by this PRX**, using neutral typedef names and explanatory parameter names. They are not a reconstructed original SDK header.

### Core loader and lifetime functions

| Engine role / conventional description | RVA | Neutral typedef / call label | Use |
|---|---:|---|---|
| Find asset header, `DB_FindXAssetHeader`-like | `0x005B6590` | `FindAssetHeaderFn` | Detoured by `asset_lookup_hook`; returns the private descriptor when eligible. |
| Check default/missing asset | `0x005B6E60` | `IsDefaultAssetFn` | Detoured by `asset_default_hook`; returns 0 for the private load only. |
| Load/link script, `Scr_LoadScript`-like | `0x007DAC10` | `LoadScriptFn` | Detoured by `load_script_hook`; stock and custom calls use the original-function stub. |
| Resolve script function handle | `0x007DA7E0` | `GetFunctionHandleFn`, `get_function_handle` | Direct call after custom linking; lookup by script name and canonical token. |
| Execute script thread with self object | `0x007E28C0` | `ExecuteThreadFn` | Detoured by `exec_thread_hook`; launches the private `main`. |
| Remove VM object reference, `RemoveRefToObject`-like | `0x007DF9E0` | `RemoveObjectReferenceFn`, `remove_object_reference` | Direct call to release the custom returned thread-object reference. Also used by stock code on other VM objects. |
| Native thread-identity import thunk | `0x00B17270` | `CurrentThreadIdFn`, `current_thread_id` | Direct call for engine-thread checks and allocator selection. Exact imported API name is not established here. |
| Zone load routine | `0x00569F30` | `LoadZoneFn` | Detoured by `zone_load_hook`; reservation follows normal return. |
| Zone allocator | `0x008C69A0` | `AllocateZoneMemoryFn` | Direct call with `(capacity, 16, 0, 5)`. |
| Pool owner release | `0x008C6D20` | `ReleasePoolOwnerFn` | Detoured by `pool_release_hook`; invalidates owned state before normal release. |

```c
typedef void *(*FindAssetHeaderFn)(
    int assetType, const char *name, int allowDefault);

typedef int (*IsDefaultAssetFn)(int assetType, const char *name);

typedef uint32_t (*LoadScriptFn)(
    const char *scriptName, void *callerScratch, uint32_t depth);

typedef uint32_t (*GetFunctionHandleFn)(
    const char *scriptName, uint32_t canonicalFunctionToken);

typedef uint16_t (*ExecuteThreadFn)(
    uint32_t codeOffset, uint32_t selfObject, uint32_t argumentCount);

typedef void (*RemoveObjectReferenceFn)(uint32_t objectId);
typedef uintptr_t (*CurrentThreadIdFn)(void);

typedef void (*LoadZoneFn)(void *blocks, void *zone);
typedef void *(*AllocateZoneMemoryFn)(
    size_t size, size_t alignment, int physicalType, int allocationType);
typedef void (*ReleasePoolOwnerFn)(
    void *pools, void *owner, unsigned poolIndex);
```

Important argument and result distinctions:

- **Load/link:** RDI is the script name; RSI is a live scratch pointer supplied by the stock caller; EDX is depth. The result is a script-object value in EAX, with zero treated as failure. This is not a one-argument `LoadScript(name)` interface.
- **Handle resolution:** the second argument is integer token `0x267`, not a pointer to the C string `"main"`. Zero indicates no acceptable code offset. The implementation additionally rejects offsets above `INT32_MAX`, outside the VM range, or outside the current payload.
- **Execution:** EDI is the VM-relative code offset, ESI is the VM self-object ID, and EDX is the number of already-prepared VM arguments. This implementation passes zero arguments and the current level object. The self-object ID is not a `gentity *`, `gclient *` or client-slot index.
- **Reference release:** the returned `uint16_t` is widened to `uint32_t` when released. The original stock thread reference is returned unchanged to the engine caller, which releases that reference itself.
- **Allocator:** the engine owns the returned bytecode allocation. It is not passed to the PRX's `free()`.

### DVAR support used by the PRX/GSC handoff

| Role | RVA | Existing PRX contract |
|---|---:|---|
| Find DVAR | `0x00118520` | `void *(*FindDvarFn)(const char *name)` |
| Set DVAR from string | `0x00119D50` | `void *(*SetDvarStringFn)(const char *name, const char *value, int source)` |
| Existing native UI render hook | `0x003DB1C0` | `void (*RenderUiFn)(int a1, void *a2, int a3, void *a4)` |

`set_client_dvar()` checks that the named DVAR already exists, then calls the setter with source **1**. GSC `setdvar`, builtin ID `0x0017`, enters native RVA `0x006A7200` and reaches the same setter with source **2** at call site `0x006A7336`. The render hook polls acknowledgements and publishes DVAR values; it does not execute a GSC entrypoint.

### Additional VM reversing anchors

These explain the native VM path. They are **not additional installed loader hooks**.

| RVA | Observed role / signature confidence |
|---|---|
| `0x002450F0` | MP script initialization/loading routine. Its complete callable ABI is not declared by this loader. |
| `0x005BBF60` | Raw-buffer decompression/copy helper called at `0x007DAF4E`; loader prepares a compressed-buffer view, destination and capacity. Full original prototype is not asserted. |
| `0x007E7B00` | Interpreter entry reached from the thread executor at `0x007E2993`; call setup passes thread object in EDI, bytecode pointer in RSI and argument count in EDX. No direct PRX invocation or complete public prototype is claimed. |
| `0x007E3580` | Integer VM argument reader. Inferred effective contract: `int32_t f(uint32_t index)`, EDI → EAX. Checks the argument count and integer type 6. |
| `0x007E3710` | Numeric VM argument reader. Inferred effective contract: `float f(uint32_t index)`, EDI → XMM0. Accepts float type 5 or converts integer type 6. |
| `0x007E37C0` | Interned-string VM argument reader. Inferred effective contract: `uint32_t f(uint32_t index)`, EDI → EAX. **Returns a string token, not a `char *`.** |
| `0x007E41E0` | Publishes a C string to the VM, `Scr_AddString`-like. RDI supplies the string; it interns it and writes a type-2 VM value. No meaningful C return value is relied upon. |
| `0x007E4380` | Publishes a vector to the VM, `Scr_AddVector`-like. RDI supplies a pointer to vector data; it creates a type-4 VM value. No meaningful C return value is relied upon. |

The string-token distinction is visible at `0x006A7225`–`0x006A723D`: `setdvar` calls `0x007E37C0`, then uses the returned integer to locate string bytes through the table pointer at `0x0ECA1D58`. Describing this getter as returning a native C string would give the wrong ABI.
