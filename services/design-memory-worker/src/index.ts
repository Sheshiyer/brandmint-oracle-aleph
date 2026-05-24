import { pollNvidiaModels, getSelectedModel, embedWithNvidia } from "./nvidia";
import {
  assetMatchesFilters,
  buildAssetEmbeddingText,
  buildSearchEmbeddingText,
  cosineSimilarity,
  inferAspect,
  stableAssetKey,
  stableVectorKey,
} from "./vector";
import type { DesignAssetRecord, Env, SearchRequest, SearchResult, StoredAssetRecord, StoredVector } from "./types";

const ASSET_LIST_KEY = "asset-list";

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function requireAdmin(request: Request, env: Env): Response | null {
  if (!env.ADMIN_TOKEN) return null;
  const expected = `Bearer ${env.ADMIN_TOKEN}`;
  if (request.headers.get("Authorization") !== expected) {
    return json({ error: "Unauthorized" }, 401);
  }
  return null;
}

async function getAssetList(env: Env): Promise<string[]> {
  return ((await env.DESIGN_KV.get(ASSET_LIST_KEY, "json")) as string[] | null) ?? [];
}

async function setAssetList(env: Env, items: string[]): Promise<void> {
  await env.DESIGN_KV.put(ASSET_LIST_KEY, JSON.stringify([...new Set(items)].sort()));
}

async function handleIngest(request: Request, env: Env): Promise<Response> {
  const unauthorized = requireAdmin(request, env);
  if (unauthorized) return unauthorized;

  const body = (await request.json()) as { records?: DesignAssetRecord[] };
  const records = body.records ?? [];
  const selected = await getSelectedModel(env);
  if (!selected) return json({ error: "No NVIDIA embedding model available" }, 503);

  const existing = await getAssetList(env);
  const next = new Set(existing);
  const ingested: string[] = [];

  for (const record of records) {
    const aspect = record.aspect ?? inferAspect(record.width, record.height);
    const embeddingInput = buildAssetEmbeddingText({ ...record, aspect });
    const vector = await embedWithNvidia(env, selected, embeddingInput);
    const stored: StoredAssetRecord = {
      ...record,
      aspect,
      embeddingModel: selected.id,
      embeddingModality: selected.modality,
      updatedAt: new Date().toISOString(),
    };
    delete (stored as Partial<DesignAssetRecord>).imageDataUri;

    await env.DESIGN_KV.put(stableAssetKey(record.sha256), JSON.stringify(stored));
    await env.DESIGN_KV.put(stableVectorKey(record.sha256), JSON.stringify({ sha256: record.sha256, vector } satisfies StoredVector));
    next.add(record.sha256);
    ingested.push(record.sha256);
  }

  await setAssetList(env, [...next]);
  return json({ ingested, model: selected });
}

async function handleSearch(request: Request, env: Env): Promise<Response> {
  const body = (await request.json()) as SearchRequest;
  if (!body.query?.trim()) return json({ error: "query is required" }, 400);

  const selected = await getSelectedModel(env);
  if (!selected) return json({ error: "No NVIDIA embedding model available" }, 503);

  const queryVector = await embedWithNvidia(env, selected, buildSearchEmbeddingText(body));
  const list = await getAssetList(env);
  const results: SearchResult[] = [];

  for (const sha256 of list) {
    const [asset, vector] = await Promise.all([
      env.DESIGN_KV.get(stableAssetKey(sha256), "json") as Promise<StoredAssetRecord | null>,
      env.DESIGN_KV.get(stableVectorKey(sha256), "json") as Promise<StoredVector | null>,
    ]);
    if (!asset || !vector) continue;
    if (!assetMatchesFilters(asset, body)) continue;
    results.push({ score: cosineSimilarity(queryVector, vector.vector), asset });
  }

  results.sort((a, b) => b.score - a.score);
  return json({ model: selected, results: results.slice(0, body.limit ?? 8) });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({ ok: true, service: "brandmint-design-memory" });
    }
    if (url.pathname === "/models/poll" && request.method === "POST") {
      const unauthorized = requireAdmin(request, env);
      if (unauthorized) return unauthorized;
      return json(await pollNvidiaModels(env));
    }
    if (url.pathname === "/models" && request.method === "GET") {
      return json({ selected: await getSelectedModel(env) });
    }
    if (url.pathname === "/ingest" && request.method === "POST") {
      return handleIngest(request, env);
    }
    if (url.pathname === "/search" && request.method === "POST") {
      return handleSearch(request, env);
    }

    return json({ error: "Not found" }, 404);
  },
};

export { chooseEmbeddingModel } from "./nvidia";
export { cosineSimilarity, inferAspect, buildAssetEmbeddingText, stableAssetKey, stableVectorKey } from "./vector";
