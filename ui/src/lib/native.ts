/**
 * Native file-system and dialog helpers for Tauri.
 *
 * Each function guards on `isTauri()` so callers don't need to.
 * In a browser context the functions return null / no-op gracefully.
 */

import { isTauri } from "./tauri";

/** Open a native folder picker dialog. Returns the selected path or null. */
export async function pickFolder(): Promise<string | null> {
  if (!isTauri()) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const selected = await open({ directory: true, title: "Select Brand Folder" });
  return selected as string | null;
}

/** Open a native file picker filtered to YAML files. */
export async function pickYamlFile(): Promise<string | null> {
  if (!isTauri()) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const selected = await open({
    title: "Select brand-config.yaml",
    filters: [{ name: "YAML", extensions: ["yaml", "yml"] }],
  });
  return selected as string | null;
}

/** Open a native file picker filtered to Markdown files. */
export async function pickMarkdownFile(): Promise<string | null> {
  if (!isTauri()) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const selected = await open({
    title: "Select product.md",
    filters: [{ name: "Markdown", extensions: ["md"] }],
  });
  return selected as string | null;
}

/** Read a text file at the given absolute path via Tauri fs plugin. */
export async function readTextFile(path: string): Promise<string> {
  if (!isTauri()) throw new Error("Not in Tauri environment");
  const { readTextFile: read } = await import("@tauri-apps/plugin-fs");
  return read(path);
}

/** Open the given path in macOS Finder / system file manager. */
export async function openInFinder(path: string): Promise<void> {
  if (!isTauri()) return;
  const { Command } = await import("@tauri-apps/plugin-shell");
  await Command.create("open", [path]).execute();
}
