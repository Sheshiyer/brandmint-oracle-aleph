import { describe, expect, it } from "vitest";
import { buildAssetEmbeddingText, cosineSimilarity, inferAspect, stableAssetKey, stableVectorKey } from "../src/vector";

describe("vector utilities", () => {
  it("calculates cosine similarity", () => {
    expect(cosineSimilarity([1, 0], [1, 0])).toBe(1);
    expect(cosineSimilarity([1, 0], [0, 1])).toBe(0);
  });

  it("infers common aspect ratios", () => {
    expect(inferAspect(1024, 1024)).toBe("1:1");
    expect(inferAspect(1920, 1080)).toBe("16:9");
    expect(inferAspect(1080, 1920)).toBe("9:16");
  });

  it("builds deterministic KV keys", () => {
    expect(stableAssetKey("abc")).toBe("asset:abc");
    expect(stableVectorKey("abc")).toBe("vector:abc");
  });

  it("builds embedding text from metadata", () => {
    const text = buildAssetEmbeddingText({
      sha256: "abc",
      path: "/x.png",
      name: "x.png",
      source: "reference",
      brand: "Newsense",
      tags: ["glass", "blue"],
      flows: ["hero"],
    });
    expect(text).toContain("brand:Newsense");
    expect(text).toContain("tag:glass");
    expect(text).toContain("flow:hero");
  });
});
