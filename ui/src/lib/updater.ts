import { checkDesktopUpdate, installDesktopUpdate } from "../api";
import { PRODUCT_VERSION } from "./appMeta";
import { isTauri } from "./tauri";

export type DesktopUpdateMetadata = {
  currentVersion: string;
  version: string;
  date?: string | null;
  body?: string | null;
};

type GithubReleasePayload = {
  tag_name?: string;
  body?: string | null;
  published_at?: string | null;
};

function normalizeVersion(version: string | null | undefined): string {
  return (version || "").trim().replace(/^v/i, "");
}

type ParsedVersion = {
  parts: number[];
  prerelease: string | null;
};

function parseVersion(version: string): ParsedVersion {
  const normalized = normalizeVersion(version);
  const [core, prerelease] = normalized.split("-", 2);
  const parts = core
    .split(".")
    .map((part) => Number.parseInt(part, 10))
    .filter((part) => Number.isFinite(part));

  return {
    parts,
    prerelease: prerelease || null,
  };
}

export function compareSemver(left: string, right: string): number {
  const a = parseVersion(left);
  const b = parseVersion(right);
  const length = Math.max(a.parts.length, b.parts.length, 3);

  for (let index = 0; index < length; index += 1) {
    const delta = (a.parts[index] || 0) - (b.parts[index] || 0);
    if (delta !== 0) {
      return delta;
    }
  }

  if (a.prerelease && !b.prerelease) return -1;
  if (!a.prerelease && b.prerelease) return 1;
  if (a.prerelease && b.prerelease) {
    return a.prerelease.localeCompare(b.prerelease);
  }

  return 0;
}

export function parseGithubReleaseUpdate(
  payload: GithubReleasePayload,
  currentVersion = PRODUCT_VERSION,
): DesktopUpdateMetadata | null {
  const latestVersion = normalizeVersion(payload.tag_name);
  const activeVersion = normalizeVersion(currentVersion);

  if (!latestVersion || compareSemver(latestVersion, activeVersion) <= 0) {
    return null;
  }

  return {
    currentVersion: activeVersion,
    version: latestVersion,
    date: payload.published_at || null,
    body: payload.body?.trim() || null,
  };
}

export async function fetchDesktopUpdate(): Promise<DesktopUpdateMetadata | null> {
  if (isTauri()) {
    return checkDesktopUpdate<DesktopUpdateMetadata | null>();
  }

  const response = await fetch(
    "https://api.github.com/repos/Sheshiyer/brandmint-oracle-aleph/releases/latest",
    {
      headers: {
        Accept: "application/vnd.github.v3+json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`GitHub release check failed: ${response.status}`);
  }

  const payload = (await response.json()) as GithubReleasePayload;
  return parseGithubReleaseUpdate(payload);
}

export async function installPendingDesktopUpdate(): Promise<void> {
  await installDesktopUpdate();
}
