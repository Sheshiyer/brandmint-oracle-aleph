import { create } from "zustand";
import type { ReferenceImage } from "../types";

export interface ReferenceState {
  references: ReferenceImage[];
  referencesLoading: boolean;
  selectedReferenceIds: string[];
  referenceLimit: number;
  refPage: number;
  refPerPage: number;
  refSearchQuery: string;

  setReferences: (r: ReferenceImage[]) => void;
  setReferencesLoading: (l: boolean) => void;
  setSelectedReferenceIds: (ids: string[]) => void;
  toggleReferenceSelection: (id: string) => void;
  setReferenceLimit: (n: number) => void;
  setRefPage: (p: number) => void;
  setRefPerPage: (pp: number) => void;
  setRefSearchQuery: (q: string) => void;
}

export const useReferenceStore = create<ReferenceState>((set) => ({
  references: [],
  referencesLoading: false,
  selectedReferenceIds: [],
  referenceLimit: 30,
  refPage: 1,
  refPerPage: 24,
  refSearchQuery: "",

  setReferences: (r) => set({ references: r }),
  setReferencesLoading: (l) => set({ referencesLoading: l }),
  setSelectedReferenceIds: (ids) => set({ selectedReferenceIds: ids }),
  toggleReferenceSelection: (id) =>
    set((s) => ({
      selectedReferenceIds: s.selectedReferenceIds.includes(id)
        ? s.selectedReferenceIds.filter((x) => x !== id)
        : [...s.selectedReferenceIds, id],
    })),
  setReferenceLimit: (n) => set({ referenceLimit: n }),
  setRefPage: (p) => set({ refPage: p }),
  setRefPerPage: (pp) => set({ refPerPage: pp }),
  setRefSearchQuery: (q) => set({ refSearchQuery: q }),
}));
