# MWR PS4 GSC reference

Technical documentation of how a PRX integrates a compiled GSC script with the native loader and scripting VM in **Call of Duty: Modern Warfare Remastered multiplayer 1.15, PS4 / CUSA05379**.

The reference covers native function contracts, engine RVAs, hook signatures, structures, memory ownership, loading and execution, builtin mappings, and opcode dispatch. It describes the supplied implementation at revision **2.25.10**, using neutral names for local helpers and private configuration values.

**Start with the [complete technical reference](docs/reference.md), or browse by topic below.**

## Target and evidence

| Item | Value |
|---|---|
| Platform | PS4, x86-64, little-endian |
| Game | MWR multiplayer 1.15 / CUSA05379 |
| Reviewed implementation | Revision 2.25.10 |
| Executable | `default_mp.elf`, 13,704,058 bytes |
| Executable SHA-256 | `450b0586c88babbd760f11f18f11dde18862629cd127a865f5ed662c730e2540` |
| Reference prepared | 15 October 2026 |

The documentation was prepared from supplied source, compiler/profile data, the compiled payload, verification records, and the executable. The recorded static checks matched 13 hook/call-site signatures, 7 call targets, 5 lifecycle writes and 69 builtin registration records. The opcode appendix records 92 allowed dispatch entries.

Those checks establish specific byte and mapping matches. They do not establish original debug-symbol names, all opcode semantics, or a new successful console run. See [source map and evidence](docs/evidence.md) for the verification scope.

## How the integration works

The PRX reserves bytecode storage through the engine's zone allocator. At a selected stock script-loading boundary, it temporarily exposes a private `ScriptFile` to the native loader, links the compiled script, and resolves its `main` handle. After the stock start-gametype callback, it invokes that handle on the level object through the native thread executor. The game's VM then owns normal script execution, waiting, scheduling, and builtin calls.

The [execution sequence](docs/execution.md) includes a diagram and the individual gates. The [memory section](docs/memory.md) explains why the bytecode allocation must satisfy the engine's program-range and ownership requirements.

## Documentation

| Topic | Contents |
|---|---|
| [Address conventions](docs/address-conventions.md) | Exact image, RVA conversion, naming confidence, script handles |
| [Native functions](docs/native-functions.md) | Loader, allocator, DVAR and VM contracts; calling convention |
| [Hooks and signatures](docs/hooks.md) | Six entry detours, selected call sites, expected bytes |
| [Globals and structures](docs/structures.md) | ScriptFile, VM globals, zone pools, DVAR fields |
| [Loading and execution](docs/execution.md) | Initialization, linking window, private asset, startup and acknowledgement |
| [Memory ownership](docs/memory.md) | Arena checks, allocation lifetime, retained packages |
| [Compiler and VM](docs/compiler-and-vm.md) | Package format, limits, validation and builtin dispatch |
| [PRX/GSC communication](docs/communication.md) | DVAR handshake and context generations |
| [Restarts and updates](docs/lifecycle.md) | Full loads, quick restarts, replacement, disarming and unloading |
| [Diagnostics](docs/diagnostics.md) | Stage evidence and runtime/package rejection codes |
| [Modes and boundaries](docs/scope.md) | Legacy modes, standalone mode and compatibility limits |
| [Evidence](docs/evidence.md) | Source roles, checks performed and qualifications |
| [Builtin mapping](docs/builtins.md) | 69 accepted bindings, IDs and native/registration RVAs |
| [Opcode mapping](docs/opcodes.md) | 92 allowed opcodes, widths and dispatch destinations |
| [Source fingerprints](docs/fingerprints.md) | SHA-256 identifiers for the reviewed evidence |

## Searchable data

The [data directory](data/README.md) contains CSV tables for loader functions and their PRX typedef contracts, DVAR helpers, native signatures, VM and zone globals, builtins, opcodes, and source fingerprints. [Combined JSON](data/reference.json) includes all tables and the source document's checksum.

Keep the address spaces separate: a native RVA is relative to the engine image, while a script handle is relative to the VM program base. The builtin table describes VM callbacks; opcode destinations are internal interpreter labels. Read the relevant section before treating an address as a callable native API.

## Maintaining the reference

`docs/reference.md` is the canonical document. Topic pages and data tables are generated from it with Python 3.9 or later, using only the standard library:

```sh
python3 tools/build_reference.py
python3 tools/build_reference.py --check
```

The check detects stale generated files, broken local Markdown links, and unclosed code fences. It checks repository consistency; the executable verification described in the reference is a separate recorded activity. See [CONTRIBUTING.md](CONTRIBUTING.md) for the evidence expected with corrections.
