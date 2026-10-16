[Repository](../README.md) · [Complete reference](reference.md#1-address-and-naming-conventions)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
