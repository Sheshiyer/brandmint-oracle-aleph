# Lessons

## 2026-03-08 - Tauri sidecar startup must not have UI bypasses

- If the desktop UI depends on the bridge sidecar, never ship a splash screen that times out to `ready` or offers a "continue anyway" bypass.
- For Tauri startup gating, always verify both layers:
  - Rust side must emit authoritative `ready` / failure status.
  - Frontend side must health-check on startup so it does not miss an early `ready` event and fall back to unsafe behavior.
- Verification requirement for future Tauri startup work:
  - one regression test for blocked startup when the sidecar never becomes healthy
  - one regression test for normal reveal when health succeeds
  - at least one real `tauri build` or equivalent compile path after Rust-side startup changes
