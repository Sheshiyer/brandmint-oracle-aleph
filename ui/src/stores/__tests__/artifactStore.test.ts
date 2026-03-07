import { describe, it, expect, beforeEach } from "vitest";
import { useArtifactStore } from "../artifactStore";

describe("artifactStore", () => {
  beforeEach(() => {
    useArtifactStore.setState(useArtifactStore.getInitialState());
  });

  it("starts with empty artifacts", () => {
    expect(useArtifactStore.getState().artifacts).toEqual([]);
  });

  it("sets artifacts", () => {
    const items = [
      {
        name: "logo.png",
        path: "/out/logo.png",
        relativePath: "logo.png",
        size: 1024,
        modifiedAt: "2025-01-01",
        extension: "png",
        group: "images",
      },
    ];
    useArtifactStore.getState().setArtifacts(items);
    expect(useArtifactStore.getState().artifacts).toHaveLength(1);
    expect(useArtifactStore.getState().artifacts[0].name).toBe("logo.png");
  });

  it("appends artifacts with a cap of 400", () => {
    const make = (n: string) => ({
      name: n,
      path: `/${n}`,
      relativePath: n,
      size: 100,
      modifiedAt: "2025-01-01",
      extension: "txt",
      group: "misc",
    });

    // Set initial batch
    const initial = Array.from({ length: 390 }, (_, i) => make(`file-${i}`));
    useArtifactStore.getState().setArtifacts(initial);

    // Append more — should cap at 400
    const extra = Array.from({ length: 20 }, (_, i) => make(`extra-${i}`));
    useArtifactStore.getState().appendArtifacts(extra);
    expect(useArtifactStore.getState().artifacts.length).toBeLessThanOrEqual(400);
  });
});
