import { create } from "zustand";
import type { ConfigDraft, ExtractedDraft, RecentProject } from "../types";
import { emptyExtraction } from "../types";
import { defaultConfigDraft } from "../lib/utils";

export interface ProjectState {
  projectName: string;
  brandFolder: string;
  scenario: string;
  waves: string;
  configPath: string;
  productMdPath: string;
  productMdText: string;
  extraction: ExtractedDraft;
  extractionConfirmed: boolean;
  configDraft: ConfigDraft;
  wizardStep: number;
  exportedAt: string;
  lastSavedAt: string;
  recentProjects: RecentProject[];
  wikiHandoffDone: boolean;
  astroHandoffDone: boolean;

  setProjectName: (name: string) => void;
  setBrandFolder: (path: string) => void;
  setScenario: (s: string) => void;
  setWaves: (w: string) => void;
  setConfigPath: (p: string) => void;
  setProductMdPath: (p: string) => void;
  setProductMdText: (t: string) => void;
  setExtraction: (e: ExtractedDraft) => void;
  updateExtraction: (partial: Partial<ExtractedDraft>) => void;
  setExtractionConfirmed: (c: boolean) => void;
  setConfigDraft: (d: ConfigDraft) => void;
  updateConfigDraft: (fn: (prev: ConfigDraft) => ConfigDraft) => void;
  setWizardStep: (s: number) => void;
  setExportedAt: (ts: string) => void;
  setLastSavedAt: (ts: string) => void;
  setRecentProjects: (p: RecentProject[]) => void;
  addRecentProject: (p: RecentProject) => void;
  setWikiHandoffDone: (done: boolean) => void;
  setAstroHandoffDone: (done: boolean) => void;
  clearDraft: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projectName: "brandmint",
  brandFolder: "./brandmint",
  scenario: "focused",
  waves: "1-7",
  configPath: "./brand-config.yaml",
  productMdPath: "./product.md",
  productMdText: "",
  extraction: emptyExtraction,
  extractionConfirmed: false,
  configDraft: defaultConfigDraft(),
  wizardStep: 0,
  exportedAt: "",
  lastSavedAt: "",
  recentProjects: [],
  wikiHandoffDone: false,
  astroHandoffDone: false,

  setProjectName: (name) => set({ projectName: name }),
  setBrandFolder: (path) => set({ brandFolder: path }),
  setScenario: (s) => set({ scenario: s }),
  setWaves: (w) => set({ waves: w }),
  setConfigPath: (p) => set({ configPath: p }),
  setProductMdPath: (p) => set({ productMdPath: p }),
  setProductMdText: (t) => set({ productMdText: t }),
  setExtraction: (e) => set({ extraction: e }),
  updateExtraction: (partial) =>
    set((s) => ({ extraction: { ...s.extraction, ...partial } })),
  setExtractionConfirmed: (c) => set({ extractionConfirmed: c }),
  setConfigDraft: (d) => set({ configDraft: d }),
  updateConfigDraft: (fn) => set((s) => ({ configDraft: fn(s.configDraft) })),
  setWizardStep: (s) => set({ wizardStep: s }),
  setExportedAt: (ts) => set({ exportedAt: ts }),
  setLastSavedAt: (ts) => set({ lastSavedAt: ts }),
  setRecentProjects: (p) => set({ recentProjects: p }),
  addRecentProject: (p) =>
    set((s) => ({
      recentProjects: [p, ...s.recentProjects.filter((x) => x.path !== p.path)].slice(0, 10),
    })),
  setWikiHandoffDone: (done) => set({ wikiHandoffDone: done }),
  setAstroHandoffDone: (done) => set({ astroHandoffDone: done }),
  clearDraft: () =>
    set({
      projectName: "brandmint",
      brandFolder: "./brandmint",
      scenario: "focused",
      waves: "1-7",
      configPath: "./brand-config.yaml",
      productMdPath: "./product.md",
      productMdText: "",
      extraction: emptyExtraction,
      extractionConfirmed: false,
      configDraft: defaultConfigDraft(),
      wizardStep: 0,
      exportedAt: "",
      wikiHandoffDone: false,
      astroHandoffDone: false,
    }),
}));
