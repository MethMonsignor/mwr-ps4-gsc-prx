# Lookup tables

Generated from [the complete reference](../docs/reference.md). All CSV and JSON field values are strings, including hexadecimal RVAs, IDs, lengths and flags. The JSON contains image identity and the SHA-256 of its source document.

| Dataset | Records |
|---|---:|
| [loader-functions.csv](loader-functions.csv) | 10 |
| [dvar-functions.csv](dvar-functions.csv) | 3 |
| [native-signatures.csv](native-signatures.csv) | 13 |
| [engine-globals.csv](engine-globals.csv) | 17 |
| [zone-globals.csv](zone-globals.csv) | 5 |
| [builtins.csv](builtins.csv) | 69 |
| [opcodes.csv](opcodes.csv) | 92 |
| [source-fingerprints.csv](source-fingerprints.csv) | 17 |

[Combined JSON](reference.json) contains the same records.

Native addresses are engine RVAs. Script handles are offsets from the VM program base. Builtin entries are VM callbacks, and opcode handler entries are internal interpreter destinations. Neither table establishes an ordinary C prototype for every row.

Edit `docs/reference.md`, then run `python3 tools/build_reference.py` from the repository root. Use `python3 tools/build_reference.py --check` to detect stale generated files and broken local Markdown links.
