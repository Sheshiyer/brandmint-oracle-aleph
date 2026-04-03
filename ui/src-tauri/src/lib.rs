mod sidecar;

use sidecar::SidecarState;
use std::sync::Arc;
use tauri::Emitter;

fn encode_query_param(name: &str, value: &str) -> Result<String, String> {
    let mut url = reqwest::Url::parse("http://127.0.0.1")
        .map_err(|e| format!("Failed to create URL encoder: {}", e))?;
    url.query_pairs_mut().append_pair(name, value);
    Ok(url
        .query()
        .unwrap_or_default()
        .trim_start_matches(&format!("{name}="))
        .to_string())
}

// ── Tauri Commands ──────────────────────────────────────────────

#[tauri::command]
async fn get_health(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state.health_check().await
}

#[tauri::command]
async fn get_state(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state.proxy_get("/api/state").await
}

#[tauri::command]
async fn get_logs(
    state: tauri::State<'_, Arc<SidecarState>>,
    since: Option<u64>,
) -> Result<serde_json::Value, String> {
    let path = format!("/api/logs?since={}", since.unwrap_or(0));
    state.proxy_get(&path).await
}

#[tauri::command]
async fn get_runners(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state.proxy_get("/api/runners").await
}

#[tauri::command]
async fn get_settings(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state.proxy_get("/api/settings").await
}

#[tauri::command]
async fn update_settings(
    state: tauri::State<'_, Arc<SidecarState>>,
    payload: serde_json::Value,
) -> Result<serde_json::Value, String> {
    state.proxy_post("/api/settings", payload).await
}

#[tauri::command]
async fn get_artifacts(
    state: tauri::State<'_, Arc<SidecarState>>,
    limit: Option<u32>,
) -> Result<serde_json::Value, String> {
    let path = format!("/api/artifacts?limit={}", limit.unwrap_or(400));
    state.proxy_get(&path).await
}

#[tauri::command]
async fn read_artifact(
    state: tauri::State<'_, Arc<SidecarState>>,
    path: String,
) -> Result<serde_json::Value, String> {
    let encoded = encode_query_param("path", &path)?;
    let route = format!("/api/artifacts/read?path={encoded}");
    state.proxy_get(&route).await
}

#[tauri::command]
async fn get_references(
    state: tauri::State<'_, Arc<SidecarState>>,
    limit: Option<u32>,
) -> Result<serde_json::Value, String> {
    let path = format!("/api/references?limit={}", limit.unwrap_or(1000));
    state.proxy_get(&path).await
}

#[tauri::command]
async fn save_config(
    state: tauri::State<'_, Arc<SidecarState>>,
    payload: serde_json::Value,
) -> Result<serde_json::Value, String> {
    state.proxy_post("/api/config/save", payload).await
}

#[tauri::command]
async fn start_run(
    state: tauri::State<'_, Arc<SidecarState>>,
    payload: serde_json::Value,
) -> Result<serde_json::Value, String> {
    state.proxy_post("/api/run/start", payload).await
}

#[tauri::command]
async fn abort_run(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state
        .proxy_post("/api/run/abort", serde_json::json!({}))
        .await
}

#[tauri::command]
async fn retry_run(state: tauri::State<'_, Arc<SidecarState>>) -> Result<serde_json::Value, String> {
    state
        .proxy_post("/api/run/retry", serde_json::json!({}))
        .await
}

#[tauri::command]
async fn start_publish(
    state: tauri::State<'_, Arc<SidecarState>>,
    payload: serde_json::Value,
) -> Result<serde_json::Value, String> {
    state.proxy_post("/api/publish/start", payload).await
}

#[tauri::command]
async fn load_intake(
    state: tauri::State<'_, Arc<SidecarState>>,
    payload: serde_json::Value,
) -> Result<serde_json::Value, String> {
    state.proxy_post("/api/intake/load", payload).await
}

#[tauri::command]
async fn restart_sidecar(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<SidecarState>>,
) -> Result<String, String> {
    sidecar::restart_sidecar(&app, state.inner(), "manual").await?;
    Ok("Sidecar restarted".to_string())
}

// ── App Entry Point ─────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sidecar_state = Arc::new(SidecarState::new());

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .setup({
            let state = sidecar_state.clone();
            move |app| {
                if cfg!(debug_assertions) {
                    app.handle()
                        .plugin(
                            tauri_plugin_log::Builder::default()
                                .level(log::LevelFilter::Info)
                                .build(),
                        )?;
                }

                // Spawn the Python bridge sidecar
                let app_handle = app.handle().clone();
                let state_for_spawn = state.clone();
                let state_for_watcher = state.clone();

                tauri::async_runtime::spawn(async move {
                    if let Err(e) = sidecar::spawn_sidecar(&app_handle, &state_for_spawn) {
                        log::error!("Failed to spawn sidecar: {}", e);
                        let _ = app_handle.emit("sidecar-status", serde_json::json!({
                            "status": "failed",
                            "error": e,
                        }));
                        return;
                    }

                    match sidecar::wait_for_healthy(&state_for_spawn).await {
                        Ok(()) => {
                            log::info!("Sidecar bridge is healthy and ready");
                            let _ = app_handle.emit("sidecar-status", serde_json::json!({
                                "status": "ready",
                            }));
                            if let Ok(current_state) = state_for_spawn.proxy_get("/api/state").await {
                                let _ = app_handle.emit("pipeline-state-changed", current_state);
                            }
                        }
                        Err(e) => {
                            log::error!("Sidecar failed health check: {}", e);
                            let _ = app_handle.emit("sidecar-status", serde_json::json!({
                                "status": "unhealthy",
                                "error": e,
                            }));
                        }
                    }

                    // Start background health watcher
                    sidecar::start_health_watcher(app_handle, state_for_watcher);
                });

                Ok(())
            }
        })
        .on_window_event({
            let state = sidecar_state.clone();
            move |_window, event| {
                if let tauri::WindowEvent::Destroyed = event {
                    state.shutdown();
                }
            }
        })
        .manage(sidecar_state)
        .invoke_handler(tauri::generate_handler![
            get_health,
            get_state,
            get_logs,
            get_runners,
            get_settings,
            update_settings,
            get_artifacts,
            read_artifact,
            get_references,
            save_config,
            start_run,
            abort_run,
            retry_run,
            start_publish,
            load_intake,
            restart_sidecar,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
