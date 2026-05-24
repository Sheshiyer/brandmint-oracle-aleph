import type { Env, NvidiaModel, SelectedEmbeddingModel } from "./types";

const MODEL_CACHE_KEY = "nim:models:last";
const SELECTED_MODEL_KEY = "nim:model:selected";

export function chooseEmbeddingModel(models: NvidiaModel[]): SelectedEmbeddingModel | null {
  return rankEmbeddingModels(models)[0] ?? null;
}

function rankEmbeddingModels(models: NvidiaModel[]): SelectedEmbeddingModel[] {
  const candidates = models
    .map((model) => {
      const id = model.id.toLowerCase();
      let score = 0;
      let modality: SelectedEmbeddingModel["modality"] = "text";
      const reasons: string[] = [];

      if (id.includes("embed") || id.includes("embedding")) {
        score += 40;
        reasons.push("embedding id");
      }
      if (id.includes("clip") || id.includes("multimodal") || id.includes("visual") || id.includes("vlm") || id.includes("-vl-")) {
        score += 35;
        modality = "multimodal";
        reasons.push("visual or multimodal id");
      }
      if (id.includes("image")) {
        score += 25;
        modality = modality === "multimodal" ? "multimodal" : "image";
        reasons.push("image id");
      }
      if (id.includes("nvidia") || id.includes("nv-")) {
        score += 5;
        reasons.push("nvidia model");
      }
      if (id.includes("nemoretriever") || id.includes("nemotron")) {
        score += 25;
        reasons.push("current NVIDIA embedding family");
      }
      if (id.includes("e5") || id.includes("nv-embedqa") || id.includes("llama-3.2-nv-embedqa")) {
        score += 20;
        reasons.push("known text embedding family");
      }

      return { id: model.id, score, modality, reason: reasons.join(", ") || "low-confidence candidate" };
    })
    .filter((candidate) => candidate.score >= 40)
    .sort((a, b) => b.score - a.score);

  return candidates;
}

export async function pollNvidiaModels(env: Env): Promise<{ models: NvidiaModel[]; selected: SelectedEmbeddingModel | null }> {
  const baseUrl = env.NVIDIA_BASE_URL ?? "https://integrate.api.nvidia.com/v1";
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/models`, {
    headers: { Authorization: `Bearer ${env.NVIDIA_API_KEY}` },
  });
  if (!response.ok) {
    throw new Error(`NVIDIA model polling failed: ${response.status}`);
  }
  const payload = (await response.json()) as { data?: NvidiaModel[] };
  const models = payload.data ?? [];
  const candidates = rankEmbeddingModels(models);
  let selected: SelectedEmbeddingModel | null = null;
  for (const candidate of candidates) {
    try {
      await embedWithNvidia(env, candidate, "design reference image");
      selected = candidate;
      break;
    } catch {
      // Some listed NVIDIA models are not served by the embeddings endpoint.
    }
  }
  await env.DESIGN_KV.put(MODEL_CACHE_KEY, JSON.stringify({ models, updatedAt: new Date().toISOString() }));
  if (selected) await env.DESIGN_KV.put(SELECTED_MODEL_KEY, JSON.stringify(selected));
  return { models, selected };
}

export async function getSelectedModel(env: Env): Promise<SelectedEmbeddingModel | null> {
  const cached = await env.DESIGN_KV.get(SELECTED_MODEL_KEY, "json");
  if (cached) return cached as SelectedEmbeddingModel;
  const result = await pollNvidiaModels(env);
  return result.selected;
}

export async function embedWithNvidia(env: Env, model: SelectedEmbeddingModel, input: string): Promise<number[]> {
  const baseUrl = env.NVIDIA_BASE_URL ?? "https://integrate.api.nvidia.com/v1";
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/embeddings`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.NVIDIA_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: model.id, input }),
  });
  if (!response.ok) {
    throw new Error(`NVIDIA embedding failed: ${response.status}`);
  }
  const payload = (await response.json()) as { data?: Array<{ embedding?: number[] }> };
  const vector = payload.data?.[0]?.embedding;
  if (!vector?.length) throw new Error("NVIDIA embedding response had no vector");
  return vector;
}
