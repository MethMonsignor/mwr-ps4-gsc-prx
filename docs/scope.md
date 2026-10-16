[Repository](../README.md) · [Complete reference](reference.md#11-legacy-modes-and-scope-boundaries)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
