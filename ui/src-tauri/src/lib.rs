mod events;
mod sidecar;

use sidecar::SidecarState;
use std::sync::Arc;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::{Emitter, Manager};

const APP_CONFIG_DIR: &str = "com.brandmint.desktop";

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
async fn get_references(
    state: tauri::State<'_, Arc<SidecarState>>,
    limit: Option<u32>,
) -> Result<serde_json::Value, String> {
    let path = format!("/api/references?limit={}", limit.unwrap_or(1000));
    state.proxy_get(&path).await
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
    state.shutdown();
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    sidecar::spawn_sidecar(&app, &state)?;
    match sidecar::wait_for_healthy(&state).await {
        Ok(()) => {
            let _ = app.emit("sidecar-status", serde_json::json!({
                "status": "ready",
            }));
            Ok("Sidecar restarted".to_string())
        }
        Err(e) => {
            let _ = app.emit("sidecar-status", serde_json::json!({
                "status": "unhealthy",
                "error": e.clone(),
            }));
            Err(e)
        }
    }
}

#[tauri::command]
async fn get_pipeline_events(
    state: tauri::State<'_, Arc<SidecarState>>,
    since: Option<String>,
) -> Result<serde_json::Value, String> {
    let events = state.event_store.get_events_since(since.as_deref());
    serde_json::to_value(&events).map_err(|e| format!("Failed to serialize events: {}", e))
}

#[tauri::command]
async fn subscribe_events(
    _app: tauri::AppHandle,
    state: tauri::State<'_, Arc<SidecarState>>,
    event_types: Vec<String>,
) -> Result<String, String> {
    let sub_id = state.event_store.add_subscription(event_types);
    Ok(sub_id)
}

// ── Window Management Commands ───────────────────────────────────

#[tauri::command]
async fn save_window_state(window: tauri::Window) -> Result<(), String> {
    let pos = window.outer_position().map_err(|e| e.to_string())?;
    let size = window.outer_size().map_err(|e| e.to_string())?;
    let state = serde_json::json!({
        "x": pos.x, "y": pos.y,
        "width": size.width, "height": size.height,
    });
    let config_dir = dirs::config_dir()
        .ok_or("No config dir")?
        .join(APP_CONFIG_DIR);
    std::fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;
    std::fs::write(
        config_dir.join("window-state.json"),
        serde_json::to_string_pretty(&state).unwrap(),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn restore_window_state(window: tauri::Window) -> Result<(), String> {
    let config_dir = dirs::config_dir()
        .ok_or("No config dir")?
        .join(APP_CONFIG_DIR);
    let path = config_dir.join("window-state.json");
    if path.exists() {
        let data = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
        let state: serde_json::Value =
            serde_json::from_str(&data).map_err(|e| e.to_string())?;
        if let (Some(x), Some(y)) = (state["x"].as_i64(), state["y"].as_i64()) {
            let _ = window.set_position(tauri::Position::Physical(
                tauri::PhysicalPosition {
                    x: x as i32,
                    y: y as i32,
                },
            ));
        }
        if let (Some(w), Some(h)) = (state["width"].as_u64(), state["height"].as_u64()) {
            let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize {
                width: w as u32,
                height: h as u32,
            }));
        }
    }
    Ok(())
}

#[tauri::command]
async fn toggle_always_on_top(window: tauri::Window) -> Result<bool, String> {
    let current = window.is_always_on_top().map_err(|e| e.to_string())?;
    window
        .set_always_on_top(!current)
        .map_err(|e| e.to_string())?;
    Ok(!current)
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

                // ── Native macOS menu bar ──────────────────────────
                let handle = app.handle();
                let menu = Menu::with_items(
                    handle,
                    &[
                        &Submenu::with_items(
                            handle,
                            "File",
                            true,
                            &[
                                &MenuItem::with_id(handle, "open-brand", "Open Brand Folder…", true, Some("CmdOrCtrl+O"))?,
                                &MenuItem::with_id(handle, "open-config", "Open Config File…", true, Some("CmdOrCtrl+Shift+O"))?,
                                &PredefinedMenuItem::separator(handle)?,
                                &PredefinedMenuItem::close_window(handle, None)?,
                            ],
                        )?,
                        &Submenu::with_items(
                            handle,
                            "Pipeline",
                            true,
                            &[
                                &MenuItem::with_id(handle, "start-pipeline", "Start Pipeline", true, Some("CmdOrCtrl+R"))?,
                                &MenuItem::with_id(handle, "abort-pipeline", "Abort Pipeline", true, Some("CmdOrCtrl+."))?,
                                &PredefinedMenuItem::separator(handle)?,
                                &MenuItem::with_id(handle, "publish", "Publish to NotebookLM", true, Some("CmdOrCtrl+P"))?,
                            ],
                        )?,
                        &Submenu::with_items(
                            handle,
                            "View",
                            true,
                            &[
                                &MenuItem::with_id(handle, "view-launch", "Launch", true, Some("CmdOrCtrl+1"))?,
                                &MenuItem::with_id(handle, "view-activity", "Activity Log", true, Some("CmdOrCtrl+2"))?,
                                &MenuItem::with_id(handle, "view-artifacts", "Artifacts", true, Some("CmdOrCtrl+3"))?,
                                &MenuItem::with_id(handle, "view-settings", "Settings", true, Some("CmdOrCtrl+4"))?,
                                &PredefinedMenuItem::separator(handle)?,
                                &MenuItem::with_id(handle, "toggle-sidebar", "Toggle Sidebar", true, Some("CmdOrCtrl+\\"))?,
                            ],
                        )?,
                        &Submenu::with_items(
                            handle,
                            "Window",
                            true,
                            &[
                                &PredefinedMenuItem::minimize(handle, None)?,
                                &PredefinedMenuItem::maximize(handle, None)?,
                                &MenuItem::with_id(handle, "always-on-top", "Always on Top", true, None::<&str>)?,
                                &PredefinedMenuItem::separator(handle)?,
                                &PredefinedMenuItem::fullscreen(handle, None)?,
                            ],
                        )?,
                        &Submenu::with_items(
                            handle,
                            "Help",
                            true,
                            &[
                                &MenuItem::with_id(handle, "docs", "Documentation", true, None::<&str>)?,
                                &MenuItem::with_id(handle, "github", "GitHub Repository", true, None::<&str>)?,
                            ],
                        )?,
                    ],
                )?;
                app.set_menu(menu)?;

                // ── Restore saved window position/size ────────────
                if let Some(main_window) = app.get_webview_window("main") {
                    if let Some(config_dir) = dirs::config_dir() {
                        let state_path =
                            config_dir.join(APP_CONFIG_DIR).join("window-state.json");
                        if state_path.exists() {
                            if let Ok(data) = std::fs::read_to_string(&state_path) {
                                if let Ok(ws) =
                                    serde_json::from_str::<serde_json::Value>(&data)
                                {
                                    if let (Some(x), Some(y)) =
                                        (ws["x"].as_i64(), ws["y"].as_i64())
                                    {
                                        let _ = main_window.set_position(
                                            tauri::Position::Physical(
                                                tauri::PhysicalPosition {
                                                    x: x as i32,
                                                    y: y as i32,
                                                },
                                            ),
                                        );
                                    }
                                    if let (Some(w), Some(h)) =
                                        (ws["width"].as_u64(), ws["height"].as_u64())
                                    {
                                        let _ = main_window.set_size(
                                            tauri::Size::Physical(tauri::PhysicalSize {
                                                width: w as u32,
                                                height: h as u32,
                                            }),
                                        );
                                    }
                                }
                            }
                        }
                    }
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
        .on_menu_event(|app, event| {
            match event.id().as_ref() {
                "open-brand" => {
                    let _ = app.emit("menu-action", "open-brand");
                }
                "open-config" => {
                    let _ = app.emit("menu-action", "open-config");
                }
                "start-pipeline" => {
                    let _ = app.emit("menu-action", "start-pipeline");
                }
                "abort-pipeline" => {
                    let _ = app.emit("menu-action", "abort-pipeline");
                }
                "publish" => {
                    let _ = app.emit("menu-action", "publish");
                }
                "view-launch" => {
                    let _ = app.emit("menu-action", "view-launch");
                }
                "view-activity" => {
                    let _ = app.emit("menu-action", "view-activity");
                }
                "view-artifacts" => {
                    let _ = app.emit("menu-action", "view-artifacts");
                }
                "view-settings" => {
                    let _ = app.emit("menu-action", "view-settings");
                }
                "toggle-sidebar" => {
                    let _ = app.emit("menu-action", "toggle-sidebar");
                }
                "always-on-top" => {
                    if let Some(window) = app.get_webview_window("main") {
                        if let Ok(current) = window.is_always_on_top() {
                            let _ = window.set_always_on_top(!current);
                        }
                    }
                }
                "docs" => {
                    let _ = app.emit("menu-action", "docs");
                }
                "github" => {
                    let _ = app.emit("menu-action", "github");
                }
                _ => {}
            }
        })
        .on_window_event({
            let state = sidecar_state.clone();
            move |window, event| {
                match event {
                    tauri::WindowEvent::CloseRequested { .. } => {
                        // Save window position/size before closing
                        if let (Ok(pos), Ok(size)) =
                            (window.outer_position(), window.outer_size())
                        {
                            if let Some(config_dir) = dirs::config_dir() {
                                let dir = config_dir.join(APP_CONFIG_DIR);
                                let _ = std::fs::create_dir_all(&dir);
                                let state_json = serde_json::json!({
                                    "x": pos.x, "y": pos.y,
                                    "width": size.width, "height": size.height,
                                });
                                let _ = std::fs::write(
                                    dir.join("window-state.json"),
                                    serde_json::to_string_pretty(&state_json)
                                        .unwrap_or_default(),
                                );
                            }
                        }
                    }
                    tauri::WindowEvent::Destroyed => {
                        state.shutdown();
                    }
                    _ => {}
                }
            }
        })
        .manage(sidecar_state)
        .invoke_handler(tauri::generate_handler![
            get_health,
            get_state,
            get_runners,
            get_settings,
            update_settings,
            get_artifacts,
            get_references,
            start_run,
            abort_run,
            retry_run,
            start_publish,
            load_intake,
            restart_sidecar,
            get_pipeline_events,
            subscribe_events,
            save_window_state,
            restore_window_state,
            toggle_always_on_top,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
