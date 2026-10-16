[Repository](../README.md) · [Complete reference](reference.md#12-source-map-and-evidence)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

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
