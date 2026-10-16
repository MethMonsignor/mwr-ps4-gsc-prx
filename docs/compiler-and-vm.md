[Repository](../README.md) · [Complete reference](reference.md#7-compiler-package-format-and-vm-dispatch)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
