# Contributing

Edit [docs/reference.md](docs/reference.md), then regenerate the topic pages and lookup tables:

```sh
python3 tools/build_reference.py
python3 tools/build_reference.py --check
```

Include the canonical document and any changed generated files in the same commit. Edit the README or this guide directly when updating repository navigation or contribution instructions.

## Address and contract corrections

A useful correction identifies the game version/title ID, executable SHA-256, relevant RVA or structure offset, current claim, proposed correction, and the evidence supporting it. State whether the evidence is a byte comparison, call-site analysis, source contract, host/mock result, or console observation.

Keep these distinctions explicit:

- Engine RVA, file offset, structure offset, canonical token, builtin ID, and VM-relative code handle.
- A contract used by the reviewed PRX, an inferred ABI, and a recovered original symbol.
- A callable native entry, a VM callback, and an internal interpreter dispatch destination.
- Static verification and observed runtime behavior.

Use neutral local labels and uppercase placeholders for private runtime names. Keep uncertainty visible where the evidence does not establish a full prototype or original field name. A new target executable needs its own image identity and evidence; do not silently replace this version's mappings.

Attach focused evidence descriptions or minimal relevant excerpts to corrections. The repository contains documentation and derived tables; executable dumps, compiled plugins and payloads are outside its contents.
