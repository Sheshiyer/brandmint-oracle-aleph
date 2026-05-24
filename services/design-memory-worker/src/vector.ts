import type { DesignAssetRecord, SearchRequest } from "./types";

export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length === 0 || b.length === 0 || a.length !== b.length) return 0;
  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

export function stableAssetKey(sha256: string): string {
  return `asset:${sha256}`;
}

export function stableVectorKey(sha256: string): string {
  return `vector:${sha256}`;
}

export function inferAspect(width?: number, height?: number): string | undefined {
  if (!width || !height) return undefined;
  const ratio = width / height;
  if (Math.abs(ratio - 1) < 0.04) return "1:1";
  if (Math.abs(ratio - 16 / 9) < 0.08) return "16:9";
  if (Math.abs(ratio - 9 / 16) < 0.08) return "9:16";
  if (Math.abs(ratio - 4 / 3) < 0.08) return "4:3";
  if (Math.abs(ratio - 3 / 4) < 0.08) return "3:4";
  return `${width}:${height}`;
}

export function buildAssetEmbeddingText(asset: DesignAssetRecord): string {
  return [
    asset.name,
    asset.brand ? `brand:${asset.brand}` : "",
    asset.project ? `project:${asset.project}` : "",
    asset.source ? `source:${asset.source}` : "",
    asset.assetId ? `asset:${asset.assetId}` : "",
    asset.aspect ? `aspect:${asset.aspect}` : "",
    asset.caption ?? "",
    asset.prompt ?? "",
    ...(asset.tags ?? []).map((tag) => `tag:${tag}`),
    ...(asset.flows ?? []).map((flow) => `flow:${flow}`),
    ...(asset.colors ?? []).map((color) => `color:${color}`),
  ]
    .filter(Boolean)
    .join("\n");
}

export function buildSearchEmbeddingText(request: SearchRequest): string {
  return [
    request.query,
    request.brand ? `brand:${request.brand}` : "",
    request.aspect ? `aspect:${request.aspect}` : "",
    request.flow ? `flow:${request.flow}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function assetMatchesFilters(asset: DesignAssetRecord, request: SearchRequest): boolean {
  if (request.brand && asset.brand !== request.brand) return false;
  if (request.aspect && asset.aspect !== request.aspect) return false;
  if (request.flow && !(asset.flows ?? []).includes(request.flow)) return false;
  return true;
}
