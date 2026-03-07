/**
 * Cross-platform notification helpers.
 *
 * In Tauri → uses @tauri-apps/plugin-notification.
 * In browser → falls back to the Web Notification API.
 */

import { isTauri } from "./tauri";

/** Send a native/browser notification. Silently no-ops when not permitted. */
export async function notify(title: string, body: string): Promise<void> {
  if (!isTauri()) {
    // Browser fallback
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, { body });
    }
    return;
  }
  const { sendNotification } = await import("@tauri-apps/plugin-notification");
  sendNotification({ title, body });
}

/** Request notification permission. Returns true if granted. */
export async function requestNotificationPermission(): Promise<boolean> {
  if (!isTauri()) {
    if ("Notification" in window) {
      const perm = await Notification.requestPermission();
      return perm === "granted";
    }
    return false;
  }
  const {
    requestPermission: reqPerm,
  } = await import("@tauri-apps/plugin-notification");
  const result = await reqPerm();
  return result === "granted";
}
