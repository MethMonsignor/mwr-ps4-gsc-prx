[Repository](../README.md) · [Complete reference](reference.md#8-prxgsc-communication)

<!-- Generated from docs/reference.md by tools/build_reference.py. -->

## 8. PRX/GSC communication

The private menu establishes a small DVAR protocol. The uppercase DVAR labels below describe each channel; they are not literal DVAR names. The GSC owns its HUD, button processing and ordinary script actions. The PRX supplies the local client identity and coordinates with the separate native menu.

| DVAR | Writer / direction | Role |
|---|---|---|
| `API_MARKER_DVAR` | GSC → PRX | Value `1` announces the core menu handshake API. |
| `LAUNCH_EPOCH_DVAR` | GSC → PRX | Fresh launch acknowledgement, 1–30,000 with wrap to 1. |
| `LOCAL_CLIENT_DVAR` | GSC initializes; PRX updates | Local authoritative server-client slot; initially `-1`. |
| `NATIVE_MENU_OPEN_DVAR` | GSC initializes; PRX updates | Whether the native PRX menu is open. |
| `SCRIPT_MENU_OPEN_DVAR` | GSC → PRX | Whether the GSC menu is open. |
| `STARTUP_STAGE_DVAR` | GSC → PRX | Human-readable progress such as waiting for player or HUD ready. |
| `SCRIPT_VERSION_DVAR` | GSC → PRX | Display version string; separate from package API/profile. |

Before custom execution, `standalone_next_epoch()` reads the previous epoch and predicts the next one. GSC `acknowledge_start()` performs the same bounded increment. `poll_acknowledgements()` accepts the API marker only when the observed epoch equals the current expected value and the native context generation has not changed.

This prevents an old `API_MARKER_DVAR=1` left by a previous match from proving that the new payload executed. A context reset clears acknowledgement state, the cached native menu-open value and the world bridge's settings. `menu_context()` resets its cached DVAR writes on a new context and only publishes into a ready, pinned, unreleased, acknowledged session.

World-effect and lobby/session bridges are **separate protocols** carried through additional DVARs. For example, the world bridge checks epoch, sequence and heartbeat before using its native movement hooks. It does not introduce a render-thread GSC call. The account menu's normal actions are made by the running GSC through native builtins; the current menu has no PRX account-request execution bridge.

Package API 1, profile `0xE6693E47`, the core handshake API 1, and the **2.25.10 join-recovery bridge API 2** describe different interfaces. They should not be conflated. Changing a feature bridge can require matching PRX and payload versions even when the package profile is unchanged.
