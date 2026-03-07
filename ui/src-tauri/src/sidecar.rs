use crate::events::EventStore;
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

const BRIDGE_PORT: u16 = 4191;
const HEALTH_CHECK_INTERVAL: Duration = Duration::from_secs(3);
const HEALTH_CHECK_TIMEOUT: Duration = Duration::from_secs(2);
const STARTUP_MAX_RETRIES: u32 = 30;
const STARTUP_RETRY_DELAY: Duration = Duration::from_millis(500);

pub struct SidecarState {
    bridge_url: String,
    child: Mutex<Option<Child>>,
    running: Arc<AtomicBool>,
    http_client: reqwest::Client,
    /// Shared event buffer for structured pipeline events.
    pub(crate) event_store: EventStore,
}

impl SidecarState {
    pub fn new() -> Self {
        Self {
            bridge_url: format!("http://127.0.0.1:{}", BRIDGE_PORT),
            child: Mutex::new(None),
            running: Arc::new(AtomicBool::new(false)),
            http_client: reqwest::Client::builder()
                .timeout(HEALTH_CHECK_TIMEOUT)
                .build()
                .expect("Failed to create HTTP client"),
            event_store: EventStore::new(),
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
            if let Some(mut child) = child_guard.take() {
                info!("Shutting down sidecar bridge");
                let _ = child.kill();
                let _ = child.wait();
                self.running.store(false, Ordering::SeqCst);
            }
        }
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }
}

/// Find the repo root by walking up from a starting directory,
/// looking for pyproject.toml + scripts/ as markers.
fn find_repo_root() -> Option<PathBuf> {
    // Start from CARGO_MANIFEST_DIR (set at compile time) which is src-tauri/
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let mut dir = manifest_dir.as_path();

    for _ in 0..8 {
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

/// Spawn the Python bridge as a child process.
pub fn spawn_sidecar(app: &AppHandle, state: &SidecarState) -> Result<(), String> {
    info!("Spawning brandmint-bridge sidecar...");

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

    // Load env vars from .env files
    let mut env_vars: Vec<(String, String)> = Vec::new();
    for env_path in [
        repo_root.join(".env"),
        dirs::home_dir()
            .unwrap_or_default()
            .join(".claude/.env"),
    ] {
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

    let mut cmd = Command::new(&python);
    cmd.arg(&bridge_script)
        .current_dir(&repo_root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    // Inject env vars
    for (key, val) in &env_vars {
        cmd.env(key, val);
    }

    let mut child = cmd
        .spawn()
        .map_err(|e| format!("Failed to spawn python bridge: {}", e))?;

    // Take ownership of stdout/stderr for forwarding
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    // Store the child handle for shutdown
    {
        let mut child_guard = state
            .child
            .lock()
            .map_err(|e| format!("Failed to lock child mutex: {}", e))?;
        *child_guard = Some(child);
    }
    state.running.store(true, Ordering::SeqCst);

    // Forward stdout to structured Tauri events
    let app_stdout = app.clone();
    let es_stdout = state.event_store.clone();
    if let Some(stdout) = stdout {
        std::thread::spawn(move || {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        info!("[bridge] {}", line);

                        // Try to parse as structured JSON with a "type" field
                        if let Ok(parsed) = serde_json::from_str::<Value>(&line) {
                            if let Some(evt_type) = parsed.get("type").and_then(|t| t.as_str()).map(String::from) {
                                let event = EventStore::create_event(&evt_type, parsed);
                                es_stdout.push_and_emit(&app_stdout, event);
                                continue;
                            }
                        }

                        // Plain text line → pipeline-log
                        let event = EventStore::create_event(
                            "log",
                            serde_json::json!({ "message": line, "level": "info" }),
                        );
                        es_stdout.push_and_emit(&app_stdout, event);
                    }
                    Err(_) => break,
                }
            }
        });
    }

    // Forward stderr to structured Tauri events
    let app_stderr = app.clone();
    let running = state.running.clone();
    let es_stderr = state.event_store.clone();
    if let Some(stderr) = stderr {
        std::thread::spawn(move || {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                match line {
                    Ok(line) => {
                        warn!("[bridge:err] {}", line);
                        let event = EventStore::create_event(
                            "log",
                            serde_json::json!({ "message": line, "level": "error" }),
                        );
                        es_stderr.push_and_emit(&app_stderr, event);
                    }
                    Err(_) => break,
                }
            }
            // stderr closed → process likely died
            running.store(false, Ordering::SeqCst);
            let event = EventStore::create_event(
                "sidecar_status",
                serde_json::json!({ "status": "terminated", "code": -1 }),
            );
            es_stderr.push_and_emit(&app_stderr, event);
        });
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

/// Background watcher that detects sidecar death and emits a restart event.
/// Does NOT auto-restart — the frontend decides whether to restart.
pub fn start_health_watcher(app: AppHandle, state: Arc<SidecarState>) {
    tokio::spawn(async move {
        // Wait for initial startup to complete
        tokio::time::sleep(Duration::from_secs(5)).await;

        loop {
            tokio::time::sleep(HEALTH_CHECK_INTERVAL).await;

            if !state.is_running() {
                let _ = app.emit(
                    "sidecar-status",
                    serde_json::json!({
                        "status": "stopped",
                    }),
                );
                tokio::time::sleep(Duration::from_secs(10)).await;
                continue;
            }

            match state.health_check().await {
                Ok(_) => {
                    // All good
                }
                Err(e) => {
                    error!("Health check failed: {}", e);
                    let _ = app.emit(
                        "sidecar-status",
                        serde_json::json!({
                            "status": "unhealthy",
                            "error": e,
                        }),
                    );
                }
            }
        }
    });
}
