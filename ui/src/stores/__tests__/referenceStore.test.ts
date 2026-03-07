import { describe, it, expect, beforeEach } from "vitest";
import { useReferenceStore } from "../referenceStore";

describe("referenceStore", () => {
  beforeEach(() => {
    useReferenceStore.setState(useReferenceStore.getInitialState());
  });

  it("starts with empty references", () => {
    expect(useReferenceStore.getState().references).toEqual([]);
  });

  it("toggles reference selection on and off", () => {
    useReferenceStore.getState().toggleReferenceSelection("ref-1");
    expect(useReferenceStore.getState().selectedReferenceIds).toContain("ref-1");

    useReferenceStore.getState().toggleReferenceSelection("ref-1");
    expect(useReferenceStore.getState().selectedReferenceIds).not.toContain("ref-1");
  });

  it("sets reference limit", () => {
    useReferenceStore.getState().setReferenceLimit(50);
    expect(useReferenceStore.getState().referenceLimit).toBe(50);
  });

  it("sets search query", () => {
    useReferenceStore.getState().setRefSearchQuery("logo");
    expect(useReferenceStore.getState().refSearchQuery).toBe("logo");
  });
});
