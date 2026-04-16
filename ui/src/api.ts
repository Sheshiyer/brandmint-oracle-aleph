import { apiBridge, bridgeAssetUrl, isTauri, listenEvent } from "./lib/tauri";

export { bridgeAssetUrl, isTauri, listenEvent };

export function getHealth<T = unknown>() {
  return apiBridge<T>("get_health");
}

export function getPipelineState<T = unknown>() {
  return apiBridge<T>("get_state");
}

export function getLogs<T = unknown>(since = 0) {
  return apiBridge<T>("get_logs", { since });
}

export function getRunners<T = unknown>() {
  return apiBridge<T>("get_runners");
}

export function getIntegrationSettings<T = unknown>() {
  return apiBridge<T>("get_settings");
}

export function updateIntegrationSettings<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("update_settings", { payload });
}

export function getArtifacts<T = unknown>(limit = 400) {
  return apiBridge<T>("get_artifacts", { limit });
}

export function readArtifact<T = unknown>(path: string) {
  return apiBridge<T>("read_artifact", { path });
}

export function getReferences<T = unknown>(limit = 1000) {
  return apiBridge<T>("get_references", { limit });
}

export function saveConfigDocument<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("save_config", { payload });
}

export function startPipelineRun<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("start_run", { payload });
}

export function abortPipelineRun<T = unknown>() {
  return apiBridge<T>("abort_run", { payload: {} });
}

export function retryPipelineRun<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("retry_run", { payload });
}

export function startPublishStage<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("start_publish", { payload });
}

export function loadIntake<T = unknown>(payload: Record<string, unknown>) {
  return apiBridge<T>("load_intake", { payload });
}

export async function checkDesktopUpdate<T = unknown>() {
  if (!isTauri()) {
    throw new Error("Desktop update checks are only available in the Tauri app.");
  }
  return apiBridge<T>("check_for_update");
}

export async function installDesktopUpdate<T = unknown>() {
  if (!isTauri()) {
    throw new Error("Desktop update install is only available in the Tauri app.");
  }
  return apiBridge<T>("install_update");
}

export async function restartSidecar<T = unknown>() {
  if (!isTauri()) {
    throw new Error("Manual sidecar restart is only available in the Tauri app.");
  }
  return apiBridge<T>("restart_sidecar");
}
