use log::{error, info};
use reqwest::Url;
use serde::Serialize;
use std::sync::Mutex;
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};
use tauri_plugin_updater::{Update, UpdaterExt};

const UPDATE_EVENT: &str = "updater-status";
const UPDATE_PRIMARY_BASE_URL: &str = "https://brandmintupdates.thoughtseed.space";
const UPDATE_FALLBACK_BASE_URL: &str =
    "https://pub-1a0540bfbd114ca7aa86f0abdfbe154f.r2.dev";
const UPDATE_DEFAULT_CHANNEL: &str = "stable";
const UPDATE_PUBKEY: &str = "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEZGRDZDQ0JGNjQzQUUyQkUKUldTKzRqcGt2OHpXLzYzZHNQYks2OW9JT0JGQXVSY3JPYnAzVWUzbEhmTEFuak9MQjVDd3J2S1IK";

#[derive(Default)]
pub struct PendingUpdate(pub Mutex<Option<Update>>);

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateMetadata {
    pub current_version: String,
    pub version: String,
    pub date: Option<String>,
    pub body: Option<String>,
}

#[derive(Clone, Serialize)]
#[serde(tag = "event", content = "data", rename_all = "camelCase")]
enum UpdateEvent {
    Checking {
        current_version: String,
    },
    Available(UpdateMetadata),
    NotAvailable {
        current_version: String,
    },
    Started {
        version: String,
        content_length: Option<u64>,
    },
    Progress {
        version: String,
        downloaded: u64,
        chunk_length: usize,
        content_length: Option<u64>,
    },
    Finished {
        version: String,
    },
    Installed {
        version: String,
    },
    Error {
        stage: String,
        message: String,
    },
}

fn emit_event(app: &AppHandle, payload: UpdateEvent) {
    let _ = app.emit(UPDATE_EVENT, payload);
}

fn emit_error(app: &AppHandle, stage: &str, message: String) {
    error!("Updater {} failed: {}", stage, message);
    emit_event(
        app,
        UpdateEvent::Error {
            stage: stage.to_string(),
            message,
        },
    );
}

fn format_update(update: &Update) -> UpdateMetadata {
    UpdateMetadata {
        current_version: update.current_version.clone(),
        version: update.version.clone(),
        date: update.date.map(|value| value.to_string()),
        body: update.body.clone(),
    }
}

fn update_channel() -> &'static str {
    option_env!("BRANDMINT_UPDATE_CHANNEL").unwrap_or(UPDATE_DEFAULT_CHANNEL)
}

fn update_primary_base_url() -> &'static str {
    option_env!("BRANDMINT_UPDATE_PRIMARY_BASE_URL").unwrap_or(UPDATE_PRIMARY_BASE_URL)
}

fn update_fallback_base_url() -> &'static str {
    option_env!("BRANDMINT_UPDATE_BASE_URL").unwrap_or(UPDATE_FALLBACK_BASE_URL)
}

fn build_update_endpoint(base_url: &str, channel: &str) -> Result<Url, String> {
    let base_url = base_url.trim().trim_end_matches('/');
    let channel = channel.trim().trim_matches('/');
    if base_url.is_empty() {
        return Err("Updater base URL cannot be empty.".to_string());
    }
    if channel.is_empty() {
        return Err("Updater channel cannot be empty.".to_string());
    }

    let endpoint = format!("{base_url}/{channel}/latest.json");
    endpoint
        .parse::<Url>()
        .map_err(|error| format!("Invalid updater endpoint URL {endpoint}: {error}"))
}

fn resolve_update_endpoints() -> Result<Vec<Url>, String> {
    let channel = update_channel();
    let mut endpoints = Vec::new();

    for base_url in [update_primary_base_url(), update_fallback_base_url()] {
        let endpoint = build_update_endpoint(base_url, channel)?;
        if !endpoints.iter().any(|existing| existing == &endpoint) {
            endpoints.push(endpoint);
        }
    }

    if endpoints.is_empty() {
        return Err("No updater endpoints configured.".to_string());
    }

    Ok(endpoints)
}

#[tauri::command]
pub async fn check_for_update(
    app: AppHandle,
    pending_update: State<'_, PendingUpdate>,
) -> Result<Option<UpdateMetadata>, String> {
    let current_version = app.package_info().version.to_string();
    emit_event(
        &app,
        UpdateEvent::Checking {
            current_version: current_version.clone(),
        },
    );

    let endpoints = resolve_update_endpoints().map_err(|message| {
        emit_error(&app, "configure", message.clone());
        message
    })?;

    let updater = app
        .updater_builder()
        .pubkey(UPDATE_PUBKEY)
        .endpoints(endpoints)
        .map_err(|error| {
            let message = format!("Invalid updater endpoint config: {}", error);
            emit_error(&app, "configure", message.clone());
            message
        })?
        .timeout(Duration::from_secs(20))
        .build()
        .map_err(|error| {
            let message = format!("Unable to initialize updater: {}", error);
            emit_error(&app, "build", message.clone());
            message
        })?;

    let update = updater.check().await.map_err(|error| {
        let message = format!("Unable to check for updates: {}", error);
        emit_error(&app, "check", message.clone());
        message
    })?;

    let mut guard = pending_update.0.lock().map_err(|error| {
        let message = format!("Unable to access updater state: {}", error);
        emit_error(&app, "state", message.clone());
        message
    })?;

    if let Some(update) = update {
        let metadata = format_update(&update);
        info!(
            "Updater found version {} (current {})",
            metadata.version, metadata.current_version
        );
        *guard = Some(update);
        emit_event(&app, UpdateEvent::Available(metadata.clone()));
        Ok(Some(metadata))
    } else {
        info!("No desktop update available for {}", current_version);
        *guard = None;
        emit_event(
            &app,
            UpdateEvent::NotAvailable {
                current_version,
            },
        );
        Ok(None)
    }
}

#[tauri::command]
pub async fn install_update(
    app: AppHandle,
    pending_update: State<'_, PendingUpdate>,
) -> Result<(), String> {
    let update = {
        let mut guard = pending_update.0.lock().map_err(|error| {
            let message = format!("Unable to access updater state: {}", error);
            emit_error(&app, "state", message.clone());
            message
        })?;
        guard.take()
    };

    let Some(update) = update else {
        let message = "No pending update. Run a fresh update check first.".to_string();
        emit_error(&app, "install", message.clone());
        return Err(message);
    };

    let version = update.version.clone();
    let mut downloaded = 0_u64;
    let mut started = false;

    update
        .download_and_install(
            |chunk_length, content_length| {
                downloaded += chunk_length as u64;
                if !started {
                    started = true;
                    emit_event(
                        &app,
                        UpdateEvent::Started {
                            version: version.clone(),
                            content_length,
                        },
                    );
                }
                emit_event(
                    &app,
                    UpdateEvent::Progress {
                        version: version.clone(),
                        downloaded,
                        chunk_length,
                        content_length,
                    },
                );
            },
            || {
                emit_event(
                    &app,
                    UpdateEvent::Finished {
                        version: version.clone(),
                    },
                );
            },
        )
        .await
        .map_err(|error| {
            let message = format!("Unable to install update {}: {}", version, error);
            emit_error(&app, "install", message.clone());
            message
        })?;

    info!("Installed desktop update {}", version);
    emit_event(&app, UpdateEvent::Installed { version });
    Ok(())
}
