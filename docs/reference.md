# MWR 1.15 PRX ↔ GSC technical reference

**Target:** PS4 multiplayer **1.15 / CUSA05379**. **Reviewed implementation revision:** 2.25.10.  
**Prepared:** 15 October 2026.  
**Basis:** the supplied PRX source, compiler, compiled payload, verification records and `default_mp.elf`. No online sources were used.

**Naming convention:** This reference uses neutral labels for local PRX helpers, types and state. Private script names, runtime directory roots and communication DVAR names are represented by uppercase placeholders. They are descriptive references, not literal configuration values or recovered engine symbols. Engine RVAs, call contracts, byte signatures, builtin IDs and structure offsets retain their verified values.

The current PRX integrates a private script, identified here as **`PRIVATE_SCRIPT_NAME`**, into the game's existing script loader and VM. It reserves bytecode storage through the engine's zone allocator, temporarily supplies a synthetic `ScriptFile` during a native load/link call, resolves the script's `main` handle, and executes it after the stock start-gametype callback. The engine then runs the script's threads, waits, native calls and HUD operations.

This is a description of the existing implementation, not a claim that a new console build was run. Static checks performed for this document matched the supplied executable's **13 hook/call-site signatures, 7 call targets, 5 lifecycle writes and 69 builtin registration records**. Appendix B records the 92 allowed opcode dispatch entries. Reading those entries does not independently prove every opcode's semantics.

## Contents

1. [Address and naming conventions](#1-address-and-naming-conventions)
2. [Native functions and callable signatures](#2-native-functions-and-callable-signatures)
3. [Hook sites, byte signatures and detours](#3-hook-sites-byte-signatures-and-detours)
4. [Engine globals and structure layouts](#4-engine-globals-and-structure-layouts)
5. [Load, link and execution sequence](#5-load-link-and-execution-sequence)
6. [Memory ownership and the script arena](#6-memory-ownership-and-the-script-arena)
7. [Compiler, package format and VM dispatch](#7-compiler-package-format-and-vm-dispatch)
8. [PRX/GSC communication](#8-prxgsc-communication)
9. [Restarts, updates, disarming and unloading](#9-restarts-updates-disarming-and-unloading)
10. [Failure and diagnostic reference](#10-failure-and-diagnostic-reference)
11. [Legacy modes and scope boundaries](#11-legacy-modes-and-scope-boundaries)
12. [Source map and evidence](#12-source-map-and-evidence)

Appendices contain the complete active builtin mapping, opcode mapping, and source fingerprints.

## 1. Address and naming conventions

### Exact image identity

| Property | Value |
|---|---|
| Executable | Supplied `default_mp.elf` |
| Platform | PS4, x86-64, little-endian |
| Target | MWR multiplayer 1.15, CUSA05379 |
| File size | 13,704,058 bytes |
| ELF SHA-256 | `450b0586c88babbd760f11f18f11dde18862629cd127a865f5ed662c730e2540` |
| Reference source | Reviewed PRX integration source, revision 2.25.10 |

The addresses in this document are **relative to the detected `default_mp` engine image**, unless explicitly described as a structure offset, script token, builtin ID or file offset. They are not offsets into the PRX.

Let `B` be the loaded engine base. A native function or global at RVA `R` has runtime address `B + R`. `find_default_mp_base()` obtains candidate bases from `sceKernelGetModuleList()` and `sceKernelGetModuleInfo()`, taking `segmentInfo[0].address`. Its acceptance is based on several expected code signatures; the `default_mp` name is an additional hint, not a substitute for those comparisons. `engineBase` records the result; the arena code records its corresponding `arenaEngineBase`.

For this ELF, the relevant text and registration data have file offset `RVA + 0x4000`. The general conversion is:

```text
file_offset = segment.p_offset + (RVA - segment.p_vaddr)
```

That formula is valid only when the requested bytes fall within the segment's **file-backed** size. Many scripting globals are in the executable's large zero-initialized runtime area and do not have initialized bytes to read from the ELF file.

| Relevant mapped segment | File offset | Virtual start | File size | Memory size |
|---|---:|---:|---:|---:|
| Executable `LOAD` | `0x4000` | `0x0` | `0xC44A88` | `0xC44A88` |
| Read-only console segment, type `0x61000010` | `0xC4C000` | `0xC48000` | `0x2B6A0` | `0x2C000` |
| Writable `LOAD` | `0xC78000` | `0xC74000` | `0x30690` | `0x138A3A00` |

### Names and confidence

Three naming layers must remain separate:

| Layer | Example | Meaning |
|---|---|---|
| Neutral implementation label | `load_script_hook`, `LoadScriptFn` | Describes the supplied PRX helper or contract. The label is editorial and is not an original engine symbol. |
| Descriptive engine label | Load/link script; `Scr_LoadScript`-like | A role inferred from disassembly and call sites. Original debug-symbol spelling is not established. |
| GSC language binding | `setdvar`, `getentbynum` | The name assigned in the supplied console compiler and traced to a console builtin registration. |

The registration records establish a native address, numeric ID and flags; they do not by themselves prove an original C/C++ function name or full high-level argument contract. References such as `DB_FindXAssetHeader`-like and `RemoveRefToObject`-like below are navigation labels, not recovered symbols.

### Four different numeric identities

| Value | What it represents |
|---|---|
| `0x007DAC10` | A native function RVA; call address is `B + 0x007DAC10`. |
| `0x267` | Canonical script function-name token for `main`, used by the handle lookup. |
| `0x0017` | Console builtin ID for GSC `setdvar`; it indexes native VM dispatch. |
| Result of `get_function_handle()` | Positive bytecode offset relative to the current **VM program base**, not to `B`. |

If `P = *(uintptr_t *)(B + 0x0F79E068)` and `H` is a returned script handle, the entry bytecode address is `P + H`. Casting `H` to a C function pointer would be incorrect.

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

## 3. Hook sites, byte signatures and detours

### What is actually detoured

Standalone loading installs **six function-entry detours**: zone load, pool release, asset lookup, default-asset test, script load and thread execution. The selected stock CALL instructions are checked and used to identify callers; the implementation does not replace those individual CALL instructions.

| Function entry | PRX hook | When custom work occurs |
|---|---|---|
| `0x00569F30` | `zone_load_hook(void *, void *)` | After original zone load returns. |
| `0x008C6D20` | `pool_release_hook(void *, void *, unsigned)` | Before original release, only for the owned pool/owner/index. |
| `0x005B6590` | `asset_lookup_hook(int, const char *, int)` | Private descriptor can be returned before DB lookup; all other calls use stock lookup. |
| `0x005B6E60` | `asset_default_hook(int, const char *)` | Returns non-default only during the private, same-thread load. |
| `0x007DAC10` | `load_script_hook(const char *, void *, uint32_t)` | At the selected caller: invalidate old state before stock load, then link private script after stock load. |
| `0x007E28C0` | `exec_thread_hook(uint32_t, uint32_t, uint32_t)` | Custom launch follows normal stock start-gametype execution. |

The two caller-sensitive wrappers are marked `__attribute__((noinline))` and capture `__builtin_return_address(0)`. Their `_at(...)` helpers receive that captured return address. This is how a global function detour restricts its extra work to a specific lifecycle call.

### Selected calls and return addresses

| Purpose | CALL RVA | Expected target | Return RVA used by PRX | Stock post-call bytes |
|---|---:|---:|---:|---|
| Chosen full-load boundary | `0x0024568C` | `0x007DAC10` | `0x00245691` | `89 C3` — save EAX in EBX |
| Optional map main | `0x00679C93` | `0x007E28C0` | `0x00679C98` | `0F B7 F8` — widen AX into EDI |
| Start gametype | `0x00679CAE` | `0x007E28C0` | `0x00679CB3` | `0F B7 F8` — widen AX into EDI |

The map-main site is also used by the separate native lobby-mode preparation. **The custom menu launches only after the start-gametype site.** `_callbacksetup::codecallback_startgametype` is associated with token `0xC2`; the supplied token table names both `0xC2` and `0x267`.

The custom launch path checks the return site and zero argument count, current level object, engine scripting thread, open precache window, loaded state and arena/handle range. The **separate native mode-preparation helper** also compares the incoming stock handle with the stored map/start-gametype callback handle. Do not attribute that additional equality check to the custom launch branch itself.

### Exact expected bytes

The following bytes are copied from the project's signature manifest and were compared with the supplied ELF for this document. These are fixed-address equality checks, not wildcard AOB scans. Several routines intentionally share the same prefix, so these prefixes are not unique identifiers across a binary.

| Manifest label | RVA | Bytes | Length |
| --- | --- | --- | --- |
| `load_script` | `0x007DAC10` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 81 EC 88 00 00 00` | 20 |
| `execute_thread` | `0x007E28C0` | `55 48 89 E5 41 57 41 56 41 54 53 48 83 EC 10` | 15 |
| `asset_is_default` | `0x005B6E60` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 50` | 14 |
| `get_function_handle` | `0x007DA7E0` | `55 48 89 E5 41 57 41 56 41 54 53 41 89 F4` | 14 |
| `remove_thread_reference` | `0x007DF9E0` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 83 EC 28` | 17 |
| `first_mp_script_call` | `0x0024568C` | `E8 7F 55 59 00 89 C3` | 7 |
| `map_main_call` | `0x00679C93` | `E8 28 8C 16 00 0F B7 F8` | 8 |
| `start_gametype_call` | `0x00679CAE` | `E8 0D 8C 16 00 0F B7 F8` | 8 |
| `thread_identity_import` | `0x00B17270` | `FF 25 72 BE 15 00` | 6 |
| `find_asset` | `0x005B6590` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 83 EC 28` | 17 |
| `zone_load` | `0x00569F30` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 81 EC C8 00 00 00` | 20 |
| `zone_release` | `0x008C6D20` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 83 EC 18` | 17 |
| `zone_allocator` | `0x008C69A0` | `55 48 89 E5 41 57 41 56 41 55 41 54 53 48 83 EC 28` | 17 |

The validated prefix length is **not** a declaration of how many bytes the detour library overwrites or relocates.

### Detour API and installation behavior

The source uses:

```c
Detour_Construct(&detour, DetourMode_x64);
Detour_DetourFunction(&detour, nativeAddress, replacementHook);
Detour_Stub(&detour, NativeFunctionType, /* original arguments */);
Detour_Destroy(&detour);
```

`Detour_Stub` is the original-function call path used to avoid recursively reentering the installed hook. `standalone_install()` installs default-asset, execution and load hooks in that order, destroying already-created hooks in that group if a later installation fails. `arena_install()` similarly handles its pool-release/zone-load pair. A failure in a later group does not imply every earlier group was removed: the top-level code may retain installed arena/DB hooks with custom loading disabled.

The build links external **`libGoldHEN_Hook.a`** and uses the SDK's `Detour.h`. The shipped `verification/host_stubs/Detour.h` is only a mock interface. The provided project does not contain the production detour implementation, so its exact jump encoding, stolen-instruction length, relocation algorithm and page-permission machinery cannot be established from this source package. This document does not invent those details.

## 4. Engine globals and structure layouts

All global addresses in the following tables are engine RVAs: read at `B + RVA`. Structure field offsets are explicitly relative to the structure pointer.

### Script loading, execution and dispatch globals

| RVA | Access width / interpretation | Use in this implementation or observed engine path |
|---|---|---|
| `0x0EC99880` | 8-byte native thread identity | Expected script-loading/startup thread. Compared with the thread-identity import result. |
| `0x0EC9D8C8` | 32-bit VM root ID | One of three required live linking roots. Its exact original field name is not asserted. |
| `0x0EC9D8CC` | 32-bit VM root ID | Second linking root. |
| `0x0EC9D8D0` | 32-bit VM root ID | Third linking root. |
| `0x0EC9D8E4` | 32-bit length | Current allowed VM program range; stock initialization writes `0x200000`. It is not the payload's bytecode length. |
| `0x0EC9D8EA` | 1-byte flag | Script loading/linking active. Set at `0x0024511F`, cleared at `0x002474B4`. |
| `0x0F79E068` | 8-byte pointer | VM program base `P`. Used to convert function pointers to/from code handles. |
| `0x0F79E020` | 32-bit VM object ID | Current level self object for startup execution. |
| `0x0AFE9CB8` | 32-bit code handle | Optional stock map-main handle. |
| `0x0AFE9CF0` | 32-bit code handle | Stock start-gametype callback handle. |
| `0x0ACFE8B0` | 32-bit flag | Precaching allowed. Set at `0x00671AB7`, cleared at `0x0067A6A5`. |
| `0x0EC9D8F0` | Array of 8-byte function pointers | VM builtin-function dispatch: index `builtinId - 1`. |
| `0x0EC9F130` | Array of 8-byte function pointers | VM builtin-method dispatch: index `builtinId - 0x8000`. |
| `0x0F7C6E28` | 8-byte VM stack pointer | Current native argument/result stack position, observed in native dispatch/getters. Not written directly by the loader. |
| `0x0F7C6E34` | 32-bit argument count | Set by builtin dispatch and read by argument getters. Not an entrypoint the PRX uses to fabricate calls. |
| `0x0ECA1D58` | 8-byte pointer | Interned-string storage base used by observed string-token consumers. |
| `0x00B8CD64` | Table of signed 32-bit relative displacements | Opcode dispatch table; entry index is `opcode - 0x1D`. |

The three roots are initialized and later released inside the stock routine at `0x002450F0`. The PRX checks them for nonzero values; it does not create replacement roots or extend their lifetime.

### `ScriptFile` — 40 bytes, 64-bit layout

```c
typedef struct ScriptFile {
    const char *name;        // +0x00
    int32_t compressedLen;  // +0x08
    int32_t len;            // +0x0C
    int32_t bytecodeLen;    // +0x10
                            // +0x14: 4 bytes of alignment padding
    const char *buffer;     // +0x18
    char *bytecode;          // +0x20
} ScriptFile;             // sizeof == 0x28
```

| Field | Meaning in the custom descriptor |
|---|---|
| `name` | Persistent PRX-owned private-name string, represented by `PRIVATE_SCRIPT_NAME`, with no `.gsc` or `.gscbin` suffix. |
| `compressedLen` | Length of the zlib-wrapped serialized script metadata stream. |
| `len` | Decompressed metadata length. This “raw stack” is serialized linking data, not a native thread stack or the live VM value stack. |
| `bytecodeLen` | Actual code length, distinct from the reserved arena capacity. |
| `buffer` | Pointer into retained package bytes, immediately after the 16-byte file header. |
| `bytecode` | Changed from the package's pristine-code pointer to the checked engine arena before native linking. |

The source asserts `sizeof == 0x28`, `buffer == +0x18` and `bytecode == +0x20` at compile time. The engine reads the code pointer at `0x007DAF53`, so supplying compressed metadata alone does not relocate the bytecode into the VM's accepted range.

### Zone/pool globals and partial layouts

| Global RVA | Width | Observed use |
|---|---|---|
| `0x1102BC88` | Start of two pool records | Script allocation pools, stride `0x530`. |
| `0x07E87E70` | 1 byte, bit 0 | Allocation-context rejection gate. |
| `0x07E87E68` | 1 byte, bit 0 | Enables the alternate allocator selector path. |
| `0x07E87E6C` | 32-bit selector | Alternate pool index; must be 0 or 1. |
| `0x0EC998B8` | 8-byte thread identity | Thread comparison used by that alternate selector. This differs from the script-thread global at `0x0EC99880`. |

Pool record at `B + 0x1102BC88 + index * 0x530`:

| Offset | Width | Meaning used by the PRX |
|---|---|---|
| `+0x00` | pointer | Current owner identity |
| `+0x08` | `uint32_t` | Entry count; bounded to 32 |
| `+0x10` | pointer | Pool region base |
| `+0x28` | `size_t` | Pool region capacity; required to equal `0x100000` |
| `+0x30` | entries | Slot array, stride `0x28` |

Slot at `pool + 0x30 + slotIndex * 0x28`:

| Offset | Width | Meaning used by the PRX |
|---|---|---|
| `+0x00` | pointer | Owner identity |
| `+0x08` | pointer | Allocation start |
| `+0x10` | pointer | Allocation cursor |
| `+0x18` | pointer | Committed end |

These are partial observed layouts; unlisted fields are deliberately unspecified. The zone record has a bounded name at **`zone + 0x20`**, occupying at most 64 bytes. That address is also the owner identity used here. The block descriptor supplies the stock script block pointer at **`blocks + 0x80`** and its length at **`blocks + 0x88`**.

### DVAR fields used by marker polling

| Relative offset | Width | Meaning |
|---|---|---|
| `dvar + 0x08` | byte | Type: 5 is integer; 7 is string in the paths supported by `read_marker()`. |
| `dvar + 0x10` | 4 bytes or pointer | Current value union: `int32_t` for type 5; `const char *` for type 7. |

The reader accepts only bounded printable strings with a terminator. A truncated prefix does not count as a matching acknowledgement. VM value type numbers and DVAR type numbers are separate enums: for example, the VM integer getter checks type **6**, while this DVAR reader checks integer type **5**.

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

## 7. Compiler, package format and VM dispatch

### Source-to-runtime path

The editable menu script and weapon catalogue feed the build. It generates the weapon script, combines both scripts into one standalone source, compiles that source, packages it, validates it, and publishes `payload.gscbin` only after successful checks.

The supplied `console_probe` uses the H1 compiler context with a restricted, explicit console opcode/builtin mapping. It replaces the inherited PC builtin maps. The numeric opcode assignments come from the included S1 PlayStation table and have been checked against the MWR image's dispatch table for the supported profile.

The standalone profile **does not permit far-script calls**. Although the compiler source contains some far-call mappings for other uses, `generate_profile.py` explicitly excludes them from the accepted update profile. The compiler's wider recognition set must not be confused with what an installed PRX will accept.

### Current package limits and shipped measurements

| Item | Accepted limit | Shipped 2.25.10 payload |
|---|---:|---:|
| Bytecode | 32,768 bytes | 29,005 bytes |
| Raw serialized stack/metadata | 65,535 bytes | 38,157 bytes |
| Function exports | 256 | 145 |
| Opcode kinds | 92 allowed | 91 emitted |
| Console builtin IDs | 69 allowed | Full allowed set in Appendix A; not a claim all are emitted |
| Packaged file size | At most 98,362 bytes | 67,221 bytes |
| Package ABI/API | 1 | 1 |
| Profile ID | `0xE6693E47` | `0xE6693E47` |
| Container CRC32 | Per file | `0x5ED918FE` |

The 98,362-byte ceiling is `16 + 11 + 65,535 + 32,768 + 32`, approximately **96.057 KiB**. It is a maximum valid **packaged binary** size, not a `.gsc` source-text size limit. The separate 8 MiB generic file-read bound does not expand the standalone profile's accepted size. The current bytecode headroom is 3,763 bytes.

Payload SHA-256: `869cd14f73c32d14f074d0b2c2a9e1ad6bf81dc7e966afccdcad20c62e540669`.

### Binary container and footer

All integer fields are little-endian except the zlib Adler32, which is big-endian.

| Position | Size | Meaning |
|---|---:|---|
| `+0x00` | 4 | `GSC\0` magic |
| `+0x04` | 4 | Compressed metadata length `C` |
| `+0x08` | 4 | Raw metadata length `R` |
| `+0x0C` | 4 | Bytecode length `N` |
| `+0x10` | `C` | Standard zlib stream containing one final stored DEFLATE block |
| `+0x10 + C` | `N` | Pristine console bytecode; first byte `0x58` (`OP_End`) |
| `+0x10 + C + N` | 32 | PRX compatibility footer |

The stored stream is `78 01 01`, followed by LEN16, one's-complement NLEN16, raw metadata and a big-endian Adler32; consequently `C = R + 11`. The PRX can inspect this bounded raw metadata without linking an additional zlib decoder. The engine still receives a normal compressed ScriptFile buffer.

Footer, relative to its own start:

| Offset | Size | Value |
|---|---:|---|
| `+0x00` | 8 | `4D 33 47 53 43 56 31 00` (eight exact bytes) |
| `+0x08` | 4 | API 1 |
| `+0x0C` | 4 | Profile `0xE6693E47` |
| `+0x10` | 4 | Container length, excluding footer |
| `+0x14` | 4 | CRC32 of container |
| `+0x18` | 4 | Main canonical token `0x267` |
| `+0x1C` | 4 | CRC32 of first 28 footer bytes |

The engine consumes the descriptor's lengths and pointers; it never consumes this footer. CRCs and the profile ID provide integrity/compatibility checks, not cryptographic authentication.

### Function records, linking data and instruction validation

The validator starts code parsing at offset 1, after the prefix `OP_End`. Each function consumes a serialized metadata record with a 32-bit code length and 16-bit export token. Token zero introduces a null-terminated export name; nonzero tokens use the canonical table. The first export must be `main` token `0x267`, later exports must be unique, and total exports are limited to 256.

String instructions contain zero, unlinked 32-bit operands and consume null-terminated strings from the serialized metadata. Dynamic field references have their own token/name records. Native linking resolves these into runtime forms. The raw metadata must be consumed exactly.

The validator also checks supported instruction widths, function boundaries, builtin IDs and function/method classification, local-call targets, and branches within their own functions. Local calls encode a signed 24-bit displacement that must be divisible by four; the accepted target is `operandStart + displacement / 4`. These restrictions are specific to the supplied profile.

The required handshake strings must appear in string operands, but mere occurrence does **not** prove that the script executes the handshake correctly. The validator does not prove VM stack correctness, local-variable lifetimes, arbitrary script logic, game-data availability or the absence of runtime engine errors.

### How a GSC builtin becomes a native call

The binary's selected registration records are 16-byte entries. The verified fields are an 8-byte native address value at `+0`, a 16-bit builtin ID at `+8`, and 16-bit flags at `+10`; the remaining bytes are not interpreted here. The image records native locations before runtime relocation. All selected flags are zero except `getentbynum`, whose record has flags 1.

Stock initialization populates two runtime pointer tables:

```text
builtin function pointer = functionTable[builtinId - 1]
builtin method pointer   = methodTable[builtinId - 0x8000]
```

Function opcodes `0x3A`–`0x3E` encode 0–4 arguments and reach handler `0x007E8107`. The indirect call is at `0x007E8141`. Method opcodes `0x9B`–`0xA0` encode 0–5 arguments and reach handler `0x007E87D4`, with the indirect call at `0x007E885A`. Both forms read a 16-bit builtin ID. Their argument counts are derived from the opcode and stored in the VM's native argument state.

At that boundary, a builtin function behaves like a **VM callback**, typically `void callback(void)` in the relevant dispatch convention. A builtin method receives a packed entity reference in EDI, an effective `void callback(uint32_t packedEntref)` contract. Other script arguments and return values travel through the VM stack, **not through an ordinary C prototype matching the GSC syntax**. This is an observed dispatch description, not a supplied typedef for every builtin.

For example, the script-level form `hud settext("text")` does not imply a callable native prototype `settext(Hud *, const char *)` at `0x00666D10`. Likewise, the GSC builtin `setdvar` at `0x006A7200` differs from the directly callable DVAR setter at `0x00119D50`.

Selected script-level forms used by the menu:

| GSC form | Result / purpose |
|---|---|
| `setdvar(name, value)` | Publish a DVAR through the GSC builtin path. |
| `getdvarint(name)` | Integer read through the VM. |
| `getentbynum(clientNumber)` | Entity or undefined, subject to native checks. |
| `newclienthudelem(player)` | A client HUD entity. |
| `hud settext(text)` | Update HUD text/configstring state. |
| `hud setshader(material, width, height)` | Update HUD material and dimensions. |
| `self setorigin(vector)` | Update/relink the player's origin. |
| `self getplayerdata(group, path...)` | Read data through the engine's GSC data/DDL path. |
| `self setplayerdata(group, path..., value)` | Write through that path; native context and field checks still apply. |
| `self setrank(rank, prestige)` | Update session rank/prestige display; not by itself proof of persistent XP/stat writes. |

These are usage forms, not exhaustive overload specifications. Appendix A lists all 69 accepted IDs and native/registration RVAs.

## 8. PRX/GSC communication

The private menu establishes a small DVAR protocol. The uppercase DVAR labels below describe each channel; they are not literal DVAR names. The GSC owns its HUD, button processing and ordinary script actions. The PRX supplies the local client identity and coordinates with the separate native menu.

| DVAR | Writer / direction | Role |
|---|---|---|
| `API_MARKER_DVAR` | GSC → PRX | Value `1` announces the core menu handshake API. |
| `LAUNCH_EPOCH_DVAR` | GSC → PRX | Fresh launch acknowledgement, 1–30,000 with wrap to 1. |
| `LOCAL_CLIENT_DVAR` | GSC initializes; PRX updates | Local authoritative server-client slot; initially `-1`. |
| `NATIVE_MENU_OPEN_DVAR` | GSC initializes; PRX updates | Whether the native PRX menu is open. |
| `SCRIPT_MENU_OPEN_DVAR` | GSC → PRX | Whether the GSC menu is open. |
| `STARTUP_STAGE_DVAR` | GSC → PRX | Human-readable progress such as waiting for player or HUD ready. |
| `SCRIPT_VERSION_DVAR` | GSC → PRX | Display version string; separate from package API/profile. |

Before custom execution, `standalone_next_epoch()` reads the previous epoch and predicts the next one. GSC `acknowledge_start()` performs the same bounded increment. `poll_acknowledgements()` accepts the API marker only when the observed epoch equals the current expected value and the native context generation has not changed.

This prevents an old `API_MARKER_DVAR=1` left by a previous match from proving that the new payload executed. A context reset clears acknowledgement state, the cached native menu-open value and the world bridge's settings. `menu_context()` resets its cached DVAR writes on a new context and only publishes into a ready, pinned, unreleased, acknowledged session.

World-effect and lobby/session bridges are **separate protocols** carried through additional DVARs. For example, the world bridge checks epoch, sequence and heartbeat before using its native movement hooks. It does not introduce a render-thread GSC call. The account menu's normal actions are made by the running GSC through native builtins; the current menu has no PRX account-request execution bridge.

Package API 1, profile `0xE6693E47`, the core handshake API 1, and the **2.25.10 join-recovery bridge API 2** describe different interfaces. They should not be conflated. Changing a feature bridge can require matching PRX and payload versions even when the package profile is unchanged.

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

## 10. Failure and diagnostic reference

### What each stage proves

| Evidence | What it establishes |
|---|---|
| Hook installed | Expected entry signatures matched and the detour API reported success. |
| Arena reserved | The allocator result and recorded pool ownership checks passed. |
| Asset hit | A private ScriptFile request matched. Does not by itself establish linking or execution. |
| `linked=1` and valid handle | Native linking returned and the resolved entry passed range/ownership checks. |
| `launches` increased / `launch_returned` | The native executor was invoked and returned a nonzero custom reference. |
| API 1 plus the expected fresh epoch | The custom GSC executed its acknowledgement path in the current context. |
| HUD-ready stage / visible menu | Further evidence of menu initialization; not evidence that every feature or persistence operation succeeded. |

### Runtime rejection codes

| Code | Meaning |
|---|---|
| `A01` | Arena not ready |
| `A02` | Zone released |
| `A03` | Pool entry count no longer accepts the recorded slot |
| `A04` | Pool owner changed |
| `A05` | Invalid committed span |
| `A06` | Reservation outside committed span |
| `L01` | Stock load result or scratch unavailable |
| `L02` | Wrong script-loading thread |
| `L03` | Loading flag/linking roots unavailable |
| `L04` | Private script did not link |
| `V10` | Payload code outside the live VM range |
| `V11` | Main handle outside the payload or invalid |
| `E01` | Startup level object mismatch |
| `E02` | Wrong startup thread |
| `E03` | Custom thread execution returned zero |
| `E04` | Precache window closed |
| `U01` | Candidate file unavailable or incomplete |
| `U02` | Container parsing rejected |
| `U03` | Retained-buffer limit reached |
| `U04` | Retirement-record allocation failed |
| `U05` | No compatible cached payload |

### Package rejection codes

| Code | Check |
|---|---|
| `P01` | Container magic/size |
| `P02` | Footer magic, API, profile or entry token |
| `P03` | Footer checksum |
| `P04` | Code/metadata/container lengths |
| `P05` | Container checksum |
| `P06` | Stored zlib block format |
| `P07` | Metadata Adler32 |
| `P08` | Required bytecode prefix |
| `P09` | Function count/table record availability |
| `P10` | Export-name bounds/termination |
| `P11` | Main placement or canonical token range |
| `P12` | Duplicate export |
| `P13` | Function code length |
| `P14` | Unsupported or truncated opcode |
| `P15` / `P16` | Dynamic field token/name data |
| `P17` | Nonzero string operand or invalid string metadata |
| `P18` | Unsupported builtin or function/method mismatch |
| `P19` | Metadata consumption or required handshake strings |
| `P20` / `P21` | Local-call encoding/entry target |
| `P22` | Branch target outside the function or off an instruction boundary |

`arena_diagnostic.txt` records load/launch counts, private asset hits, current handle, launch/context epochs, arena address/capacity, owner/pool/slot, generation, payload CRC, retired bytes and update status. Saving this is an explicit snapshot; it is not a continuously flushed trace.

The legacy `Resume: 23 VERIFIED` display belongs to the older fixed Bog test's before/caller/resume marker sequence. It is not the standalone menu's current API/epoch protocol.

## 11. Legacy modes and scope boundaries

| Config mode | Behavior |
|---|---|
| `off` | No new custom starts/replacements; installed hooks may remain resident. |
| `probe` | Record observed ScriptFile names. |
| `capture` | Copy the selected stock descriptor buffers to owned snapshot memory; disk save occurs separately. |
| `inject` | Legacy fixed Bog replacement in the original stock bytecode allocation, with exact stock/payload checks. |
| `arena` | Legacy Bog asset replacement using a checked engine arena; still targets the stock Bog asset. |
| `standalone` | Current private-script load and launch; stock map scripts remain on their ordinary path. |

The legacy name is **`maps/mp/mp_bog`**. The current name is **`PRIVATE_SCRIPT_NAME`**. The current compatibility package is accepted only under the private standalone name. The fact that the source retains old modes does not make them interchangeable with the current payload.

The asset hook performs its immediate lookup/snapshot/replacement work without disk I/O or native VM execution. The standalone **load hook** does read the candidate file in the verified full-load window. These are different hooks; saying that no hook ever reads a file would be inaccurate.

The separate `native_online_start_at()` / `prepare_session()` path prepares native lobby/session state before the relevant stock startup call. It does not perform private script linking and is not needed to explain the VM's execution mechanism. A successful GSC acknowledgement does not establish service authentication, persistent account saves or successful spawning.

The current system does not provide unlimited-size scripts, general PC GSC compatibility, arbitrary external script dependencies, or Synergy-specific extensions such as `executeCommand` and `replaceFunc` merely by virtue of loading a private script. A new builtin/opcode allowance requires a corresponding validated compiler/profile and PRX change; changing the JSON alone cannot extend an already-installed PRX.

## 12. Source map and evidence

The table identifies evidence by its role. Local helper names are the neutral documentation labels used throughout this reference; they are not an exact source-symbol index.

| Evidence component | Relevant definitions |
|---|---|
| PRX entry, base discovery and render integration | `find_default_mp_base`, `try_install_renderer`, native typedefs, `set_client_dvar`, render polling, `plugin_load`, `plugin_unload` |
| Engine RVA definitions | Base offset aliases; contains broader inferred/VM-facing anchors that are not automatically callable native APIs |
| ScriptFile, asset interception and control state | `ScriptFile`, config/container parsing, asset hook, mode handling, markers, update UI, unload gate |
| Zone-owned script arena | Zone/pool RVAs, allocator prototypes, pool/slot checks, reservation and owner-release hooks |
| Standalone linking and launch integration | Loader/executor/default hooks, return-site gates, native prototypes/signatures, handle checks and launch |
| Payload update and retention logic | Candidate publication, generation tracking and retirement policy |
| Binary package format and validator | Package format, hard limits and C structural validator |
| Compiled console compatibility profile | Installed profile ID, accepted opcode widths/kinds and builtin IDs |
| Console profile JSON | Build-time profile and complete mapping |
| Console compiler binding definitions | Console compiler mapping and explicit builtin names |
| Canonical function-token table | Included canonical names for `main` and start-gametype tokens |
| Binary package writer, Payload build and publication pipeline | Packaging and publication pipeline |
| Primary menu script | Actual main/menu/acknowledgement and feature logic |
| Native signature manifest | Thirteen fixed-address signature records |
| Loader and VM disassembly excerpts | Original loader, handle, startup and reference-release disassembly evidence |
| Native builtin registration manifest | All 69 selected native/ID/registration mappings |
| VM dispatch and builtin investigation notes | Dispatch-table and earlier native-binding investigation; historical counts are superseded by the active profile |
| Gameplay builtin contract notes, Account builtin contract notes, World and camera native-path notes | Argument/data-path evidence for the relevant native callbacks |
| Standalone integration design notes, Payload update and lifetime notes | Existing design and update/lifetime notes |

### Verification performed for this reference

The executable SHA-256 and segment layout were read directly. All 13 manifest byte sequences matched. The three selected lifecycle CALL targets and four explanatory internal CALL targets matched their relative displacements. The loading/range/precache writes matched the recorded bytes. All 69 selected registration addresses, IDs and flags matched and agreed with the active profile. Package size, metadata length, code length, profile, footer and checksums matched the shipped payload. The profile ID was recomputed from its canonical JSON contents.

Additional argument-getter and native-dispatch descriptions come from targeted disassembly of the supplied image's code. The opcode appendix records the relative dispatch destinations read from the ELF; shared handler destinations are expected for opcode families and do not imply separate native function entries.

The supplied evidence includes host/mock test results and reports of successful multi-map/restart loading. Those are separate evidence categories. **No new PRX build, PS4 execution or live-memory dump was performed for this documentation.** The production GoldHEN detour library and complete original engine symbols were not supplied in this source package. Function/field labels and inferred contracts are qualified accordingly.

## Appendix A. Complete active console builtin mapping

These are the **69 IDs permitted by profile `0xE6693E47`**, not the entire engine's API. `Function` means VM function dispatch; `Method` means VM entity-method dispatch. The native callback does not receive ordinary C arguments corresponding to the displayed GSC name; see Section 7.

| GSC binding | Console ID | Kind | Native RVA | Registration RVA | Flags |
| --- | --- | --- | --- | --- | --- |
| `isdefined` | `0x0012` | Function | `0x006A6450` | `0x00C60860` | 0 |
| `setdvar` | `0x0017` | Function | `0x006A7200` | `0x00C608D0` | 0 |
| `getdvar` | `0x001C` | Function | `0x006A7940` | `0x00C60920` | 0 |
| `getdvarint` | `0x001D` | Function | `0x006A7B30` | `0x00C60930` | 0 |
| `getdvarfloat` | `0x001E` | Function | `0x006A7DC0` | `0x00C60940` | 0 |
| `getentbynum` | `0x0023` | Function | `0x006A8500` | `0x00C60990` | 1 |
| `spawn` | `0x0030` | Function | `0x006A9920` | `0x00C60A60` | 0 |
| `setslowmotion` | `0x003D` | Function | `0x006AB620` | `0x00C60B60` | 0 |
| `int` | `0x0048` | Function | `0x006AC410` | `0x00C60C20` | 0 |
| `anglestoforward` | `0x006A` | Function | `0x006AF6C0` | `0x00C60EA0` | 0 |
| `getsubstr` | `0x0072` | Function | `0x006B1740` | `0x00C60F80` | 0 |
| `precacheitem` | `0x007A` | Function | `0x006B2C10` | `0x00C61010` | 0 |
| `precacheshader` | `0x007B` | Function | `0x006B2CB0` | `0x00C61020` | 0 |
| `tablelookup` | `0x00C6` | Function | `0x006BF120` | `0x00C616A0` | 0 |
| `tablelookupbyrow` | `0x00C7` | Function | `0x006BF3C0` | `0x00C616C0` | 0 |
| `getentarray` | `0x00EE` | Function | `0x006F5E60` | `0x00C4DEC0` | 0 |
| `newclienthudelem` | `0x00FC` | Function | `0x006651A0` | `0x00C4DFE0` | 0 |
| `map_restart` | `0x0113` | Function | `0x00357FA0` | `0x00C4E1A0` | 0 |
| `exitlevel` | `0x0114` | Function | `0x00358060` | `0x00C4E1B0` | 0 |
| `isbot` | `0x01FC` | Function | `0x00838070` | `0x00C4E770` | 0 |
| `getrankforxp` | `0x02EA` | Function | `0x00361F60` | `0x00C4E9F0` | 0 |
| `attach` | `0x8000` | Method | `0x006CD6F0` | `0x00C61EF0` | 0 |
| `detachall` | `0x8002` | Method | `0x006CDF50` | `0x00C61F20` | 0 |
| `getattachsize` | `0x8003` | Method | `0x006CE8A0` | `0x00C61F40` | 0 |
| `getattachmodelname` | `0x8004` | Method | `0x006CEB10` | `0x00C61F50` | 0 |
| `getattachtagname` | `0x8005` | Method | `0x006CECA0` | `0x00C61F60` | 0 |
| `getattachignorecollision` | `0x8006` | Method | `0x006CEEF0` | `0x00C61F70` | 0 |
| `unlink` | `0x800E` | Method | `0x006D0150` | `0x00C62000` | 0 |
| `islinked` | `0x800F` | Method | `0x006D0210` | `0x00C62010` | 0 |
| `playerlinkto` | `0x8011` | Method | `0x006D0B10` | `0x00C62080` | 0 |
| `delete` | `0x8028` | Method | `0x006D38A0` | `0x00C621E0` | 0 |
| `setmodel` | `0x8029` | Method | `0x006D3A50` | `0x00C62200` | 0 |
| `setmovespeedscale` | `0x808C` | Method | `0x006DBF20` | `0x00C629C0` | 0 |
| `getlocalplayerprofiledata` | `0x809D` | Method | `0x006DD610` | `0x00C62B70` | 0 |
| `setlocalplayerprofiledata` | `0x809E` | Method | `0x006DDAF0` | `0x00C62B80` | 0 |
| `isitemunlocked` | `0x80B0` | Method | `0x006E1440` | `0x00C62CA0` | 0 |
| `getplayerdata` | `0x80B1` | Method | `0x006E1D60` | `0x00C62CB0` | 0 |
| `setplayerdata` | `0x80B2` | Method | `0x006E21E0` | `0x00C62CC0` | 0 |
| `setrank` | `0x80D3` | Method | `0x00658180` | `0x00C5F500` | 0 |
| `fragbuttonpressed` | `0x80E7` | Method | `0x0063EED0` | `0x00C5DF30` | 0 |
| `secondaryoffhandbuttonpressed` | `0x80E8` | Method | `0x0063F0D0` | `0x00C5DF40` | 0 |
| `setvelocity` | `0x80EA` | Method | `0x0063F550` | `0x00C5DF60` | 0 |
| `giveweapon` | `0x80EE` | Method | `0x0063FAA0` | `0x00C5DFF0` | 0 |
| `takeweapon` | `0x80EF` | Method | `0x0063FF90` | `0x00C5E000` | 0 |
| `getcurrentweapon` | `0x80F1` | Method | `0x00640380` | `0x00C5E020` | 0 |
| `hasweapon` | `0x80F4` | Method | `0x006406D0` | `0x00C5E050` | 0 |
| `switchtoweapon` | `0x80F5` | Method | `0x00640A80` | `0x00C5E060` | 0 |
| `givemaxammo` | `0x80F9` | Method | `0x006425B0` | `0x00C5E0F0` | 0 |
| `setorigin` | `0x8100` | Method | `0x006443E0` | `0x00C5E1A0` | 0 |
| `getvelocity` | `0x8101` | Method | `0x00644880` | `0x00C5E1B0` | 0 |
| `getplayerangles` | `0x8103` | Method | `0x00644A30` | `0x00C5E1D0` | 0 |
| `usebuttonpressed` | `0x8104` | Method | `0x00644D10` | `0x00C5E200` | 0 |
| `attackbuttonpressed` | `0x8105` | Method | `0x00644F10` | `0x00C5E210` | 0 |
| `adsbuttonpressed` | `0x8106` | Method | `0x00645110` | `0x00C5E220` | 0 |
| `meleebuttonpressed` | `0x8107` | Method | `0x00645310` | `0x00C5E230` | 0 |
| `disableweapons` | `0x8112` | Method | `0x006467D0` | `0x00C5E300` | 0 |
| `enableweapons` | `0x8113` | Method | `0x00646820` | `0x00C5E310` | 0 |
| `disableoffhandweapons` | `0x8114` | Method | `0x00646870` | `0x00C5E320` | 0 |
| `enableoffhandweapons` | `0x8115` | Method | `0x006468C0` | `0x00C5E330` | 0 |
| `freezecontrols` | `0x811E` | Method | `0x006476C0` | `0x00C5E3F0` | 0 |
| `setclientomnvar` | `0x812D` | Method | `0x00649C30` | `0x00C5E500` | 0 |
| `setperk` | `0x815C` | Method | `0x00650150` | `0x00C5F0F0` | 0 |
| `hasperk` | `0x815D` | Method | `0x00650590` | `0x00C5F100` | 0 |
| `unsetperk` | `0x815F` | Method | `0x00650B70` | `0x00C5F120` | 0 |
| `settext` | `0x82A4` | Method | `0x00666D10` | `0x00C5FDB0` | 0 |
| `setshader` | `0x82A6` | Method | `0x00666E60` | `0x00C5FDD0` | 0 |
| `destroy` | `0x82BA` | Method | `0x00668000` | `0x00C5FF50` | 0 |
| `getlinkedparent` | `0x83E6` | Method | `0x006D0330` | `0x00C62020` | 0 |
| `setcostumemodels` | `0x84B2` | Method | `0x006E5760` | `0x00C62FA0` | 0 |

## Appendix B. Accepted opcode widths and native dispatch anchors

`Width` includes the opcode byte. `Handler RVA` is the dispatch destination read from the supplied ELF using `tableBase + signed32(table[(opcode - 0x1D)])`, with table base `0x00B8CD64`. These destinations are internal interpreter labels, **not independent callable functions**. Names and validation kinds come from the supplied frozen compiler profile; the address read alone does not prove an operation's semantics.

| Validator kind | Meaning |
|---:|---|
| 0 | Fixed-width instruction with no additional kind-specific validation |
| 1 | Field token; may consume serialized dynamic-name metadata |
| 2 | Unlinked string operand and serialized string |
| 3 | Builtin function ID |
| 4 | Builtin method ID |
| 5 | Local call/function-reference target |
| 6 | Forward/conditional relative branch |
| 7 | Backward relative branch |
| 8 | Signed 32-bit relative jump |

| Opcode | Profile name | Width | Kind | Handler RVA |
| --- | --- | --- | --- | --- |
| `0x1D` | `OP_CastFieldObject` | 1 | 0 | `0x007EADE1` |
| `0x1E` | `OP_SetLocalVariableFieldCached` | 2 | 0 | `0x007EA987` |
| `0x1F` | `OP_plus` | 1 | 0 | `0x007EAB6A` |
| `0x20` | `OP_RemoveLocalVariables` | 2 | 0 | `0x007E890F` |
| `0x21` | `OP_EvalSelfFieldVariableRef` | 3 | 1 | `0x007E8DD2` |
| `0x23` | `OP_GetGameRef` | 1 | 0 | `0x007E8DE9` |
| `0x25` | `OP_EvalLevelFieldVariableRef` | 3 | 1 | `0x007E89CE` |
| `0x27` | `OP_greater` | 1 | 0 | `0x007EB33B` |
| `0x2A` | `OP_dec` | 1 | 0 | `0x007EBDA7` |
| `0x2B` | `OP_JumpOnTrue` | 3 | 6 | `0x007EAB45` |
| `0x2D` | `OP_equality` | 1 | 0 | `0x007EA9F4` |
| `0x30` | `OP_GetVector` | 13 | 0 | `0x007E8E88` |
| `0x32` | `OP_PreScriptCall` | 1 | 0 | `0x007E8559` |
| `0x33` | `OP_GetByte` | 2 | 0 | `0x007E85A4` |
| `0x35` | `OP_SetSelfFieldVariableField` | 3 | 1 | `0x007EB3BF` |
| `0x36` | `OP_JumpOnFalseExpr` | 3 | 6 | `0x007E8373` |
| `0x37` | `OP_GetUndefined` | 1 | 0 | `0x007E8F48` |
| `0x38` | `OP_jumpback` | 3 | 7 | `0x007E829E` |
| `0x39` | `OP_JumpOnTrueExpr` | 3 | 6 | `0x007E8684` |
| `0x3A` | `OP_CallBuiltin0` | 3 | 3 | `0x007E8107` |
| `0x3B` | `OP_CallBuiltin1` | 3 | 3 | `0x007E8107` |
| `0x3C` | `OP_CallBuiltin2` | 3 | 3 | `0x007E8107` |
| `0x3D` | `OP_CallBuiltin3` | 3 | 3 | `0x007E8107` |
| `0x3E` | `OP_CallBuiltin4` | 3 | 3 | `0x007E8107` |
| `0x41` | `OP_SetLocalVariableFieldCached0` | 1 | 0 | `0x007EAAE9` |
| `0x42` | `OP_ClearFieldVariable` | 3 | 1 | `0x007E8B10` |
| `0x43` | `OP_GetLevel` | 1 | 0 | `0x007E8E3D` |
| `0x44` | `OP_size` | 1 | 0 | `0x007E86BE` |
| `0x47` | `OP_AddArray` | 1 | 0 | `0x007EBDFB` |
| `0x49` | `OP_EvalFieldVariable` | 3 | 1 | `0x007E8474` |
| `0x4C` | `OP_Return` | 1 | 0 | `0x007E839E` |
| `0x4D` | `OP_CreateLocalVariable` | 2 | 0 | `0x007E8893` |
| `0x50` | `OP_ScriptLocalMethodCall` | 4 | 5 | `0x007EA361` |
| `0x53` | `OP_GetSelfObject` | 1 | 0 | `0x007E8C24` |
| `0x55` | `OP_SetLevelFieldVariableField` | 3 | 1 | `0x007EAE4E` |
| `0x56` | `OP_EvalArray` | 1 | 0 | `0x007EAF03` |
| `0x57` | `OP_GetSelf` | 1 | 0 | `0x007E873C` |
| `0x58` | `OP_End` | 1 | 0 | `0x007E8773` |
| `0x59` | `OP_EvalSelfFieldVariable` | 3 | 1 | `0x007E8449` |
| `0x5B` | `OP_EvalLocalVariableCached0` | 1 | 0 | `0x007E80D8` |
| `0x5C` | `OP_EvalLocalVariableCached1` | 1 | 0 | `0x007E8529` |
| `0x5D` | `OP_EvalLocalVariableCached2` | 1 | 0 | `0x007E83FB` |
| `0x5E` | `OP_EvalLocalVariableCached3` | 1 | 0 | `0x007E8863` |
| `0x5F` | `OP_EvalLocalVariableCached4` | 1 | 0 | `0x007E8A22` |
| `0x60` | `OP_EvalLocalVariableCached5` | 1 | 0 | `0x007E89A1` |
| `0x61` | `OP_EvalLocalVariableCached` | 2 | 0 | `0x007E84AA` |
| `0x64` | `OP_EvalLocalVariableObjectCached` | 2 | 0 | `0x007E81C9` |
| `0x65` | `OP_ScriptLocalThreadCall` | 5 | 5 | `0x007EA3F6` |
| `0x66` | `OP_GetInteger` | 5 | 0 | `0x007E94BA` |
| `0x67` | `OP_ScriptMethodCallPointer` | 1 | 0 | `0x007E94E0` |
| `0x68` | `OP_checkclearparams` | 1 | 0 | `0x007E8281` |
| `0x6B` | `OP_minus` | 1 | 0 | `0x007EB162` |
| `0x6C` | `OP_ScriptLocalFunctionCall2` | 4 | 5 | `0x007E85CB` |
| `0x6E` | `OP_GetNegByte` | 2 | 0 | `0x007E8D59` |
| `0x6F` | `OP_SafeCreateVariableFieldCached` | 2 | 0 | `0x007E8327` |
| `0x70` | `OP_greater_equal` | 1 | 0 | `0x007EAD26` |
| `0x71` | `OP_vector` | 1 | 0 | `0x007E923D` |
| `0x74` | `OP_ClearArray` | 1 | 0 | `0x007EBA41` |
| `0x75` | `OP_DecTop` | 1 | 0 | `0x007EAD55` |
| `0x76` | `OP_CastBool` | 1 | 0 | `0x007E842B` |
| `0x77` | `OP_EvalArrayRef` | 1 | 0 | `0x007EB1CF` |
| `0x78` | `OP_SetNewLocalVariableFieldCached0` | 2 | 0 | `0x007EAAB4` |
| `0x79` | `OP_GetZero` | 1 | 0 | `0x007E825B` |
| `0x7A` | `OP_wait` | 1 | 0 | `0x007E9705` |
| `0x7B` | `OP_waittill` | 1 | 0 | `0x007E9BC7` |
| `0x80` | `OP_EvalLocalArrayCached` | 2 | 0 | `0x007EAA09` |
| `0x83` | `OP_GetUnsignedShort` | 3 | 0 | `0x007E8AE4` |
| `0x84` | `OP_clearparams` | 1 | 0 | `0x007E90D3` |
| `0x87` | `OP_EmptyArray` | 1 | 0 | `0x007E8BDE` |
| `0x8A` | `OP_EvalFieldVariableRef` | 3 | 1 | `0x007E89DB` |
| `0x8D` | `OP_GetFloat` | 5 | 0 | `0x007E8577` |
| `0x8E` | `OP_EvalLocalVariableRefCached` | 2 | 0 | `0x007E8B96` |
| `0x8F` | `OP_JumpOnFalse` | 3 | 6 | `0x007EA950` |
| `0x93` | `OP_less` | 1 | 0 | `0x007EAA88` |
| `0x94` | `OP_BoolNot` | 1 | 0 | `0x007E870F` |
| `0x97` | `OP_GetString` | 5 | 2 | `0x007E8187` |
| `0x98` | `OP_EvalLevelFieldVariable` | 3 | 1 | `0x007E9A15` |
| `0x99` | `OP_GetLevelObject` | 1 | 0 | `0x007E948A` |
| `0x9A` | `OP_inc` | 1 | 0 | `0x007EAD6C` |
| `0x9B` | `OP_CallBuiltinMethod0` | 3 | 4 | `0x007E87D4` |
| `0x9C` | `OP_CallBuiltinMethod1` | 3 | 4 | `0x007E87D4` |
| `0x9D` | `OP_CallBuiltinMethod2` | 3 | 4 | `0x007E87D4` |
| `0x9E` | `OP_CallBuiltinMethod3` | 3 | 4 | `0x007E87D4` |
| `0x9F` | `OP_CallBuiltinMethod4` | 3 | 4 | `0x007E87D4` |
| `0xA0` | `OP_CallBuiltinMethod5` | 3 | 4 | `0x007E87D4` |
| `0xA4` | `OP_SetVariableField` | 1 | 0 | `0x007EB413` |
| `0xA6` | `OP_GetLocalFunction` | 4 | 5 | `0x007E8E0E` |
| `0xA8` | `OP_multiply` | 1 | 0 | `0x007EB367` |
| `0xAC` | `OP_EvalLocalVariableRefCached0` | 1 | 0 | `0x007EA120` |
| `0xB1` | `OP_jump` | 5 | 8 | `0x007E8701` |
| `0xB4` | `OP_inequality` | 1 | 0 | `0x007EAD01` |
| `0xB5` | `OP_ScriptLocalFunctionCall` | 4 | 5 | `0x007E85E4` |

## Appendix C. Source fingerprints

These SHA-256 values identify the principal source/evidence files used for this reference. Components are listed by their role, without project-specific filenames.

| Evidence component | SHA-256 |
| --- | --- |
| PRX entry, base discovery and render integration | `924a115d35333ab2a9def7b7ed01d1c5f43a8ee59c5e30ba04c5b9231fc10578` |
| ScriptFile, asset interception and control state | `a09adbb3e7bb6ccb04871cc9c82f9872d3c19b259e3814f0adfb143d098e07d9` |
| Zone-owned script arena | `99049a71b919656b2901ca26540d6b1f798b0a08b78a02ae8e6780bf51d80621` |
| Standalone linking and launch integration | `0d8fbc11c6e8bb41acb407faa91db81276abe230870d8774d3776f958192ad0c` |
| Binary package format and validator | `7b66a9eccf6e300c28c5352b05eaf461469d205e1587121863a2cdd217e71a07` |
| Payload update and retention logic | `7144de8831b7a2e008ba0d952df834e55ce2c760e4355220c72202168e9b5afc` |
| Compiled console compatibility profile | `becf920ab3309830e90ce39970a3a7fd6d3adfcfc30602f4ba761c51f94fd12f` |
| Console compiler binding definitions | `6b55cc137b394d9d4993e5c28ddc193c68c5aac8016e8341b1067b1b02f457b8` |
| Console profile JSON | `b64dae5d8ae05bdf67bea681911dc0c77669e6c3f7214e26d0899e8d76d00413` |
| Binary package writer | `441835d0f79dc36cde611d4fca23cca925470c301a667efaf0ba9e6524218fe0` |
| Payload build and publication pipeline | `802a062cd6581440cef0f3555d1059efbffe5a10d12650368ef80dd461922a64` |
| Native builtin registration manifest | `85927796708e042ce24bc790aa6e30a8b649854c4b37e609e66bf69ef616a3ce` |
| Native signature manifest | `7aa3805397540a45dba2ac5fc1dbc197e9b88e57416a9b81c23d0ec3fe69ad13` |
| Loader and VM disassembly excerpts | `80bfdf1bbb3a97e23975cc943205a6df86fcea05c48a120d15a648c110b0e0ad` |
| Primary menu script | `def9b02b7f4d19848bfddabbcd28aa7fcf2873c8acb6f93d9140ba1c18633611` |
| Engine RVA definitions | `ff9cdb768a93d32f8a3ea16eb7be25765a277cb52767b27ae4afce9654460a91` |
| Canonical function-token table | `f57ce727f9af767f018293e5dfcbc97ca06ac688e7c2a76e143f5da127c1fa87` |
