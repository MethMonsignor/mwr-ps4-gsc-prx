[Repository](../README.md) · [Complete reference](reference.md#10-failure-and-diagnostic-reference)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
