[Repository](../README.md) · [Complete reference](reference.md#4-engine-globals-and-structure-layouts)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
