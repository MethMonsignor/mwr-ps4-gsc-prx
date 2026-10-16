[Repository](../README.md) · [Complete reference](reference.md#3-hook-sites-byte-signatures-and-detours)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
