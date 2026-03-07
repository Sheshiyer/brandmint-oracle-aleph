//! Structured event system for pipeline state changes and sidecar communication.
//!
//! Events are buffered in a capped ring buffer for pull-based retrieval via
//! `get_pipeline_events`, and simultaneously emitted over Tauri's IPC for
//! push-based frontend subscriptions.

use serde::Serialize;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter};

// ── Event channel name constants ─────────────────────────────────

/// Emitted when the pipeline transitions between states (idle → running → done).
pub const EVT_PIPELINE_STATE: &str = "pipeline-state-changed";

/// Emitted for each log line produced by the sidecar process.
pub const EVT_PIPELINE_LOG: &str = "pipeline-log";

/// Emitted for incremental progress updates (e.g., 3/10 steps complete).
pub const EVT_PIPELINE_PROGRESS: &str = "pipeline-progress";

/// Emitted when the sidecar process status changes (ready, unhealthy, terminated).
pub const EVT_SIDECAR_STATUS: &str = "sidecar-status";

/// Maximum number of events retained in the ring buffer.
const MAX_BUFFERED_EVENTS: usize = 1000;

// ── Core event type ──────────────────────────────────────────────

/// A structured event produced by the pipeline or sidecar.
///
/// The `event_type` discriminator determines which Tauri channel the event is
/// broadcast on.  The `payload` carries arbitrary JSON specific to that type.
#[derive(Clone, Serialize, Debug)]
pub struct PipelineEvent {
    /// Discriminator: `"state_changed"`, `"log"`, `"progress"`, `"error"`, or custom.
    pub event_type: String,
    /// Arbitrary JSON payload specific to the event type.
    pub payload: serde_json::Value,
    /// Milliseconds since Unix epoch, encoded as a string for safe JS interop.
    pub timestamp: String,
}

// ── Internal subscription record ─────────────────────────────────

/// Associates a subscription ID with the set of event types the subscriber
/// is interested in receiving.
#[derive(Debug)]
#[allow(dead_code)]
struct Subscription {
    id: String,
    event_types: Vec<String>,
}

// ── EventStore ───────────────────────────────────────────────────

/// Thread-safe store that buffers recent events and tracks active subscriptions.
///
/// All interior state is wrapped in `Arc<Mutex<_>>` so that cloning the store
/// produces a handle to the **same** underlying data.  This is intentional:
/// it allows cheap sharing across the stdout reader thread, stderr reader
/// thread, and Tauri IPC command handlers without changing function signatures.
#[derive(Clone)]
pub struct EventStore {
    events: Arc<Mutex<VecDeque<PipelineEvent>>>,
    subscriptions: Arc<Mutex<Vec<Subscription>>>,
    next_sub_id: Arc<AtomicU64>,
}

impl EventStore {
    /// Create an empty event store with pre-allocated ring buffer capacity.
    pub fn new() -> Self {
        Self {
            events: Arc::new(Mutex::new(VecDeque::with_capacity(MAX_BUFFERED_EVENTS))),
            subscriptions: Arc::new(Mutex::new(Vec::new())),
            next_sub_id: Arc::new(AtomicU64::new(1)),
        }
    }

    /// Returns the current time as milliseconds since the Unix epoch (string).
    ///
    /// Using millis-since-epoch avoids pulling in `chrono` while remaining
    /// trivially comparable from both Rust and JavaScript.
    fn now_millis() -> String {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis()
            .to_string()
    }

    /// Build a [`PipelineEvent`] with an auto-generated timestamp.
    pub fn create_event(event_type: &str, payload: serde_json::Value) -> PipelineEvent {
        PipelineEvent {
            event_type: event_type.to_string(),
            payload,
            timestamp: Self::now_millis(),
        }
    }

    /// Map an `event_type` discriminator to the corresponding Tauri channel name.
    fn channel_for(event_type: &str) -> &str {
        match event_type {
            "state_changed" => EVT_PIPELINE_STATE,
            "log" => EVT_PIPELINE_LOG,
            "progress" => EVT_PIPELINE_PROGRESS,
            "sidecar_status" => EVT_SIDECAR_STATUS,
            other => other,
        }
    }

    /// Buffer the event in the ring buffer and emit it on the appropriate Tauri channel.
    ///
    /// When the buffer is full, the oldest event is silently dropped.
    pub fn push_and_emit(&self, app: &AppHandle, event: PipelineEvent) {
        // 1. Store in ring buffer
        if let Ok(mut buf) = self.events.lock() {
            if buf.len() >= MAX_BUFFERED_EVENTS {
                buf.pop_front();
            }
            buf.push_back(event.clone());
        }

        // 2. Emit over Tauri IPC on the mapped channel
        let channel = Self::channel_for(&event.event_type);
        let _ = app.emit(channel, &event);
    }

    /// Retrieve buffered events, optionally only those with a timestamp strictly
    /// greater than `since` (a millisecond Unix-epoch string).
    ///
    /// All current timestamps are 13-digit strings, so lexicographic comparison
    /// is equivalent to numeric comparison until ~year 2286.
    pub fn get_events_since(&self, since: Option<&str>) -> Vec<PipelineEvent> {
        let guard = match self.events.lock() {
            Ok(g) => g,
            Err(_) => return Vec::new(),
        };

        match since {
            Some(ts) => guard
                .iter()
                .filter(|e| e.timestamp.as_str() > ts)
                .cloned()
                .collect(),
            None => guard.iter().cloned().collect(),
        }
    }

    /// Register interest in a set of event types and return a unique subscription ID.
    ///
    /// The subscription ID can be used by the frontend to correlate or later
    /// cancel the subscription.
    pub fn add_subscription(&self, event_types: Vec<String>) -> String {
        let id = format!("sub_{}", self.next_sub_id.fetch_add(1, Ordering::Relaxed));
        if let Ok(mut subs) = self.subscriptions.lock() {
            subs.push(Subscription {
                id: id.clone(),
                event_types,
            });
        }
        id
    }
}
