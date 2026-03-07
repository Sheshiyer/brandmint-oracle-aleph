import { create } from "zustand";
import type { ArtifactItem } from "../types";

export interface ArtifactState {
  artifacts: ArtifactItem[];

  setArtifacts: (a: ArtifactItem[]) => void;
  appendArtifacts: (a: ArtifactItem[]) => void;
}

export const useArtifactStore = create<ArtifactState>((set) => ({
  artifacts: [],

  setArtifacts: (a) => set({ artifacts: a }),
  appendArtifacts: (a) =>
    set((s) => ({ artifacts: [...a, ...s.artifacts].slice(0, 400) })),
}));
