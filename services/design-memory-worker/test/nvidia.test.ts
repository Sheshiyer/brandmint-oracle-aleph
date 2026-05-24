import { afterEach, describe, expect, it, vi } from "vitest";
import { chooseEmbeddingModel, pollNvidiaModels } from "../src/nvidia";
import type { Env } from "../src/types";

function createEnv(): Env {
  const values = new Map<string, string>();
  return {
    NVIDIA_API_KEY: "test-key",
    DESIGN_KV: {
      get: vi.fn(async (key: string) => values.get(key) ?? null),
      put: vi.fn(async (key: string, value: string) => {
        values.set(key, value);
      }),
    } as unknown as KVNamespace,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("NVIDIA model selection", () => {
  it("prefers visual or multimodal embedding models", () => {
    const selected = chooseEmbeddingModel([
      { id: "nvidia/nv-embedqa-e5-v5" },
      { id: "nvidia/visual-clip-embedding" },
    ]);
    expect(selected?.id).toBe("nvidia/visual-clip-embedding");
    expect(selected?.modality).toBe("multimodal");
  });

  it("falls back to known text embedding families", () => {
    const selected = chooseEmbeddingModel([{ id: "nvidia/nv-embedqa-e5-v5" }]);
    expect(selected?.id).toBe("nvidia/nv-embedqa-e5-v5");
    expect(selected?.modality).toBe("text");
  });

  it("returns null without embedding candidates", () => {
    expect(chooseEmbeddingModel([{ id: "nvidia/llama" }])).toBeNull();
  });

  it("prefers current visual-language embedding model names", () => {
    const selected = chooseEmbeddingModel([
      { id: "nvidia/llama-3.2-nv-embedqa-1b-v1" },
      { id: "nvidia/llama-nemotron-embed-vl-1b-v2" },
    ]);
    expect(selected?.id).toBe("nvidia/llama-nemotron-embed-vl-1b-v2");
    expect(selected?.modality).toBe("multimodal");
  });

  it("validates candidates before caching selected embedding model", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/models")) {
        return Response.json({
          data: [
            { id: "nvidia/llama-nemotron-embed-vl-1b-v2" },
            { id: "nvidia/nv-embedqa-e5-v5" },
          ],
        });
      }
      const body = JSON.parse(String(init?.body));
      if (body.model === "nvidia/llama-nemotron-embed-vl-1b-v2") {
        return new Response("not found", { status: 404 });
      }
      return Response.json({ data: [{ embedding: [1, 0, 0] }] });
    });

    const result = await pollNvidiaModels(createEnv());

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(result.selected?.id).toBe("nvidia/nv-embedqa-e5-v5");
  });
});
