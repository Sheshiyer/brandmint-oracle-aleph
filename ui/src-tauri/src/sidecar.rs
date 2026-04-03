use log::{error, info, warn};
use serde_json::Value;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::AppHandle;
use tauri::Emitter;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

const BRIDGE_PORT: u16 = 4191;
const HEALTH_CHECK_TIMEOUT: Duration = Duration::from_secs(2);
const STARTUP_MAX_RETRIES: u32 = 30;
const STARTUP_RETRY_DELAY: Duration = Duration::from_millis(500);
const EVENT_SYNC_INTERVAL: Duration = Duration::from_millis(1500);

pub struct SidecarState {
    bridge_url: String,
    child: Mutex<Option<ManagedChild>>,
    running: Arc<AtomicBool>,
    restarting: Arc<AtomicBool>,
    generation: Arc<std::sync::atomic::AtomicU64>,
    http_client: reqwest::Client,
}

enum ManagedChild {
    Std(Child),
    Shell(CommandChild),
}

impl SidecarState {
    pub fn new() -> Self {
        Self {
            bridge_url: format!("http://127.0.0.1:{}", BRIDGE_PORT),
            child: Mutex::new(None),
            running: Arc::new(AtomicBool::new(false)),
            restarting: Arc::new(AtomicBool::new(false)),
            generation: Arc::new(std::sync::atomic::AtomicU64::new(0)),
            http_client: reqwest::Client::builder()
                .timeout(HEALTH_CHECK_TIMEOUT)
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    pub async fn health_check(&self) -> Result<Value, String> {
        let url = format!("{}/api/health", self.bridge_url);
        match self.http_client.get(&url).send().await {
            Ok(resp) => {
                if resp.status().is_success() {
                    resp.json::<Value>()
                        .await
                        .map_err(|e| format!("Failed to parse health response: {}", e))
                } else {
                    Err(format!("Bridge returned status {}", resp.status()))
                }
            }
            Err(e) => Err(format!("Bridge not reachable: {}", e)),
        }
    }

    /// Proxy a GET request to the Python bridge
    pub async fn proxy_get(&self, path: &str) -> Result<Value, String> {
        let url = format!("{}{}", self.bridge_url, path);
        let resp = self
            .http_client
            .get(&url)
            .send()
            .await
            .map_err(|e| format!("Bridge GET {} failed: {}", path, e))?;
        if !resp.status().is_success() {
            return Err(format!("Bridge GET {} returned {}", path, resp.status()));
        }
        resp.json::<Value>()
            .await
            .map_err(|e| format!("Failed to parse response from {}: {}", path, e))
    }

    /// Proxy a POST request to the Python bridge
    pub async fn proxy_post(&self, path: &str, body: Value) -> Result<Value, String> {
        let url = format!("{}{}", self.bridge_url, path);
        let resp = self
            .http_client
            .post(&url)
            .json(&body)
            .send()
            .await
            .map_err(|e| format!("Bridge POST {} failed: {}", path, e))?;
        if !resp.status().is_success() {
            let status = resp.status();
            let err_body = resp.text().await.unwrap_or_default();
            return Err(format!(
                "Bridge POST {} returned {}: {}",
                path, status, err_body
            ));
        }
        resp.json::<Value>()
            .await
            .map_err(|e| format!("Failed to parse response from {}: {}", path, e))
    }

    pub fn shutdown(&self) {
        if let Ok(mut child_guard) = self.child.lock() {
            if let Some(child) = child_guard.take() {
                info!("Shutting down sidecar bridge");
                match child {
                    ManagedChild::Std(mut child) => {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                    ManagedChild::Shell(child) => {
                        let _ = child.kill();
                    }
                }
                self.running.store(false, Ordering::SeqCst);
            }
        }
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    pub fn restart_in_progress(&self) -> bool {
        self.restarting.load(Ordering::SeqCst)
    }

    pub fn generation(&self) -> u64 {
        self.generation.load(Ordering::SeqCst)
    }
}

/// Find the repo root by walking up from a starting directory,
/// looking for pyproject.toml + scripts/ as markers.
fn find_repo_root() -> Option<PathBuf> {
    // Start from CARGO_MANIFEST_DIR (set at compile time) which is src-tauri/
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let mut dir = manifest_dir.as_path();

    for _ in 0..12 {
        if dir.join("pyproject.toml").exists() && dir.join("scripts").is_dir() {
            return Some(dir.to_path_buf());
        }
        dir = dir.parent()?;
    }
    None
}

/// Find python3 in common macOS locations
fn find_python() -> Result<PathBuf, String> {
    let candidates = [
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
    ];
    for path in &candidates {
        let p = PathBuf::from(path);
        if p.exists() {
            return Ok(p);
        }
    }
    // Fall back to PATH lookup
    Ok(PathBuf::from("python3"))
}

fn load_env_vars(repo_root: Option<&PathBuf>) -> Vec<(String, String)> {
    let mut env_vars: Vec<(String, String)> = Vec::new();

    let mut candidates = Vec::new();
    if let Some(root) = repo_root {
        candidates.push(root.join(".env"));
    }
    if let Some(home_dir) = dirs::home_dir() {
        candidates.push(home_dir.join(".claude/.env"));
    }

    for env_path in candidates {
        if env_path.exists() {
            if let Ok(contents) = std::fs::read_to_string(&env_path) {
                for line in contents.lines() {
                    let line = line.trim();
                    if line.is_empty() || line.starts_with('#') {
                        continue;
                    }
                    if let Some((key, val)) = line.split_once('=') {
                        let val = val.trim_matches('"').trim_matches('\'');
                        env_vars.push((key.to_string(), val.to_string()));
                    }
                }
            }
        }
    }

    if let Some(root) = repo_root {
        env_vars.push(("BRANDMINT_ROOT".to_string(), root.display().to_string()));
    }

    env_vars
}

fn spawn_dev_sidecar(app: &AppHandle, state: &SidecarState) -> Result<(), String> {
    let repo_root = find_repo_root()
        .ok_or_else(|| "Cannot find repo root (pyproject.toml + scripts/)".to_string())?;

    let bridge_script = repo_root.join("scripts/ui_backend_bridge.py");
    if !bridge_script.exists() {
        return Err(format!(
            "Bridge script not found at {}",
            bridge_script.display()
        ));
    }

    let python = find_python()?;
    info!(
        "Using python={}, script={}",
        python.display(),
        bridge_script.display()
    );

    let env_vars = load_env_vars(Some(&repo_root));

    let mut cmd = Command::new(&python);
    cmd.arg(&bridge_script)
        .current_dir(&repo_root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    for (key, val) in &env_vars {
        cmd.env(key, val);
    }

    let mut child = cmd
        .spawn()
        .map_err(|e| format!("Failed to spawn python bridge: {}", e))?;

    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    {
        let mut child_guard = state
            .child
            .lock()
            .map_err(|e| format!("Failed to lock child mutex: {}", e))?;
        *child_guard = Some(ManagedChild::Std(child));
    }
    state.running.store(true, Ordering::SeqCst);
    state.generation.fetch_add(1, Ordering::SeqCst);

    let app_stdout = app.clone();
    if let Some(stdout) = stdout {
        std::thread::spawn(move || {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        info!("[bridge] {}", line);
                        let _ = app_stdout.emit(
                            "sidecar-log",
                            serde_json::json!({
                                "level": "info",
                                "message": line,
                            }),
                        );
                    }
                    Err(_) => break,
                }
            }
        });
    }

    let app_stderr = app.clone();
    let running = state.running.clone();
    if let Some(stderr) = stderr {
        std::thread::spawn(move || {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        warn!("[bridge:err] {}", line);
                        let _ = app_stderr.emit(
                            "sidecar-log",
                            serde_json::json!({
                                "level": "error",
                                "message": line,
                            }),
                        );
                    }
                    Err(_) => break,
                }
            }
            running.store(false, Ordering::SeqCst);
            let _ = app_stderr.emit(
                "sidecar-terminated",
                serde_json::json!({ "code": -1 }),
            );
        });
    }

    Ok(())
}

fn spawn_release_sidecar(app: &AppHandle, state: &SidecarState) -> Result<(), String> {
    let env_vars = load_env_vars(None);
    let mut command = app
        .shell()
        .sidecar("brandmint-bridge")
        .map_err(|e| format!("Failed to resolve bundled sidecar: {}", e))?;

    for (key, value) in env_vars {
        command = command.env(key, value);
    }

    let (mut rx, child) = command
        .spawn()
        .map_err(|e| format!("Failed to spawn bundled sidecar: {}", e))?;

    {
        let mut child_guard = state
            .child
            .lock()
            .map_err(|e| format!("Failed to lock child mutex: {}", e))?;
        *child_guard = Some(ManagedChild::Shell(child));
    }
    state.running.store(true, Ordering::SeqCst);
    state.generation.fetch_add(1, Ordering::SeqCst);

    let app_handle = app.clone();
    let running = state.running.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let message = String::from_utf8_lossy(&line).trim().to_string();
                    if !message.is_empty() {
                        info!("[bridge] {}", message);
                        let _ = app_handle.emit(
                            "sidecar-log",
                            serde_json::json!({
                                "level": "info",
                                "message": message,
                            }),
                        );
                    }
                }
                CommandEvent::Stderr(line) => {
                    let message = String::from_utf8_lossy(&line).trim().to_string();
                    if !message.is_empty() {
                        warn!("[bridge:err] {}", message);
                        let _ = app_handle.emit(
                            "sidecar-log",
                            serde_json::json!({
                                "level": "error",
                                "message": message,
                            }),
                        );
                    }
                }
                CommandEvent::Terminated(payload) => {
                    running.store(false, Ordering::SeqCst);
                    let _ = app_handle.emit(
                        "sidecar-terminated",
                        serde_json::json!({
                            "code": payload.code.unwrap_or(-1),
                            "signal": payload.signal,
                        }),
                    );
                    break;
                }
                CommandEvent::Error(message) => {
                    running.store(false, Ordering::SeqCst);
                    let _ = app_handle.emit(
                        "sidecar-log",
                        serde_json::json!({
                            "level": "error",
                            "message": message,
                        }),
                    );
                }
                _ => {}
            }
        }
    });

    Ok(())
}

/// Spawn the Python bridge as a child process.
pub fn spawn_sidecar(app: &AppHandle, state: &SidecarState) -> Result<(), String> {
    info!("Spawning brandmint-bridge sidecar...");

    if cfg!(debug_assertions) {
        spawn_dev_sidecar(app, state)?;
    } else {
        spawn_release_sidecar(app, state)?;
    }

    info!("Sidecar spawned, waiting for health check...");
    Ok(())
}

/// Poll the bridge health endpoint until it responds.
pub async fn wait_for_healthy(state: &SidecarState) -> Result<(), String> {
    for attempt in 1..=STARTUP_MAX_RETRIES {
        match state.health_check().await {
            Ok(_) => {
                info!("Bridge healthy after {} attempts", attempt);
                return Ok(());
            }
            Err(e) => {
                if attempt == STARTUP_MAX_RETRIES {
                    return Err(format!(
                        "Bridge failed to become healthy after {} attempts: {}",
                        STARTUP_MAX_RETRIES, e
                    ));
                }
                tokio::time::sleep(STARTUP_RETRY_DELAY).await;
            }
        }
    }
    Err("Bridge health check timed out".to_string())
}

pub async fn restart_sidecar(
    app: &AppHandle,
    state: &Arc<SidecarState>,
    reason: &str,
) -> Result<(), String> {
    if state
        .restarting
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Sidecar restart already in progress".to_string());
    }

    info!("Restarting sidecar bridge ({})", reason);
    let _ = app.emit(
        "sidecar-status",
        serde_json::json!({
            "status": "starting",
            "reason": reason,
            "restarting": true,
        }),
    );

    state.shutdown();
    tokio::time::sleep(Duration::from_millis(500)).await;

    let result = match spawn_sidecar(app, state.as_ref()) {
        Ok(()) => wait_for_healthy(state.as_ref()).await,
        Err(e) => Err(e),
    };

    state.restarting.store(false, Ordering::SeqCst);

    match result {
        Ok(()) => {
            let _ = app.emit(
                "sidecar-status",
                serde_json::json!({
                    "status": "ready",
                    "reason": reason,
                    "restarted": true,
                }),
            );
            Ok(())
        }
        Err(e) => {
            let _ = app.emit(
                "sidecar-status",
                serde_json::json!({
                    "status": "unhealthy",
                    "reason": reason,
                    "error": e.clone(),
                }),
            );
            Err(e)
        }
    }
}

/// Background watcher that detects sidecar death and emits a restart event.
pub fn start_health_watcher(app: AppHandle, state: Arc<SidecarState>) {
    tokio::spawn(async move {
        // Wait for initial startup to complete
        tokio::time::sleep(Duration::from_secs(1)).await;
        let mut last_state: Option<Value> = None;
        let mut last_log_id = 0_u64;
        let mut last_generation = state.generation();

        loop {
            tokio::time::sleep(EVENT_SYNC_INTERVAL).await;

            let generation = state.generation();
            if generation != last_generation {
                last_generation = generation;
                last_state = None;
                last_log_id = 0;
            }

            if state.restart_in_progress() {
                continue;
            }

            if !state.is_running() {
                warn!("Sidecar not running, attempting automatic restart");
                last_state = None;
                last_log_id = 0;
                if let Err(e) = restart_sidecar(&app, &state, "sidecar-stopped").await {
                    error!("Automatic sidecar restart failed: {}", e);
                }
                continue;
            }

            match state.health_check().await {
                Ok(_) => {
                    // All good
                }
                Err(e) => {
                    error!("Health check failed: {}", e);
                    last_state = None;
                    last_log_id = 0;
                    if let Err(restart_error) =
                        restart_sidecar(&app, &state, "health-check-failed").await
                    {
                        error!("Automatic sidecar restart failed: {}", restart_error);
                    }
                    continue;
                }
            }

            match state.proxy_get("/api/state").await {
                Ok(current_state) => {
                    if last_state.as_ref() != Some(&current_state) {
                        let _ = app.emit("pipeline-state-changed", current_state.clone());
                        last_state = Some(current_state);
                    }
                }
                Err(e) => {
                    warn!("State sync failed: {}", e);
                }
            }

            let path = format!("/api/logs?since={last_log_id}");
            match state.proxy_get(&path).await {
                Ok(payload) => {
                    if let Some(entries) = payload.get("logs").and_then(Value::as_array) {
                        for entry in entries {
                            if let Some(id) = entry.get("id").and_then(Value::as_u64) {
                                last_log_id = id;
                            }
                            let _ = app.emit("sidecar-log", entry.clone());
                        }
                    }
                }
                Err(e) => {
                    warn!("Log sync failed: {}", e);
                }
            }
        }
    });
}
