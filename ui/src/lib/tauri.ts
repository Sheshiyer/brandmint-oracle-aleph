/**
 * Tauri environment detection and API bridge.
 *
 * When running inside Tauri, API calls use `invoke()` (IPC).
 * When running in a browser, API calls fall back to `fetch()` against localhost:4191.
 */

// @ts-expect-error — __TAURI__ is injected by Tauri runtime
export const isTauri = (): boolean => typeof window !== "undefined" && Boolean(window.__TAURI__);

const BRIDGE_BASE = "http://127.0.0.1:4191";

type BridgeRoute = {
  method: "GET" | "POST";
  path: string | ((args?: Record<string, unknown>) => string);
};

/**
 * Invoke a Tauri command or fall back to fetch() against the Python bridge.
 */
export async function apiBridge<T = unknown>(
  command: string,
  args?: Record<string, unknown>,
): Promise<T> {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(command, args);
  }

  // Fallback: map command names to REST endpoints
  const mapping: Record<string, BridgeRoute> = {
    get_health: { method: "GET", path: "/api/health" },
    get_state: { method: "GET", path: "/api/state" },
    get_logs: { method: "GET", path: (routeArgs) => `/api/logs?since=${routeArgs?.since ?? 0}` },
    get_runners: { method: "GET", path: "/api/runners" },
    get_settings: { method: "GET", path: "/api/settings" },
    update_settings: { method: "POST", path: "/api/settings" },
    get_artifacts: { method: "GET", path: (routeArgs) => `/api/artifacts?limit=${routeArgs?.limit ?? 400}` },
    read_artifact: {
      method: "GET",
      path: (routeArgs) => `/api/artifacts/read?path=${encodeURIComponent(String(routeArgs?.path ?? ""))}`,
    },
    get_references: { method: "GET", path: (routeArgs) => `/api/references?limit=${routeArgs?.limit ?? 1000}` },
    save_config: { method: "POST", path: "/api/config/save" },
    start_run: { method: "POST", path: "/api/run/start" },
    abort_run: { method: "POST", path: "/api/run/abort" },
    retry_run: { method: "POST", path: "/api/run/retry" },
    start_publish: { method: "POST", path: "/api/publish/start" },
    load_intake: { method: "POST", path: "/api/intake/load" },
  };

  const route = mapping[command];
  if (!route) {
    throw new Error(`Unknown API command: ${command}`);
  }
  const path = typeof route.path === "function" ? route.path(args) : route.path;

  const opts: RequestInit = { method: route.method };
  if (route.method === "POST" && args) {
    opts.headers = { "Content-Type": "application/json" };
    // For POST commands, the args object may contain a `payload` key
    opts.body = JSON.stringify(args.payload ?? args);
  }

  const res = await fetch(`${BRIDGE_BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as Record<string, string>).error || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function bridgeAssetUrl(pathOrUrl: string): string {
  if (!pathOrUrl) return BRIDGE_BASE;
  if (/^(https?:)?\/\//i.test(pathOrUrl) || pathOrUrl.startsWith("data:") || pathOrUrl.startsWith("blob:")) {
    return pathOrUrl;
  }
  if (pathOrUrl.startsWith("/")) {
    return `${BRIDGE_BASE}${pathOrUrl}`;
  }
  return `${BRIDGE_BASE}/${pathOrUrl.replace(/^\/+/, "")}`;
}

/**
 * Listen to Tauri events (no-op in browser mode).
 */
export async function listenEvent(
  event: string,
  handler: (payload: unknown) => void,
): Promise<() => void> {
  if (!isTauri()) {
    // In browser mode, there are no events — return a no-op unlisten
    return () => {};
  }
  const { listen } = await import("@tauri-apps/api/event");
  return listen(event, (e) => handler(e.payload));
}
