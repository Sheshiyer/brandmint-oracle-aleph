import { create } from "zustand";
import type { AppPreferences, IntegrationSettings, RunnerInfo } from "../types";
import { DEFAULT_INTEGRATION_SETTINGS, DEFAULT_PREFERENCES, FALLBACK_RUNNERS } from "../types";

export interface SettingsState {
  integrationSettings: IntegrationSettings;
  preferences: AppPreferences;
  publishStage: string;
  runners: RunnerInfo[];
  selectedRunner: string;

  setIntegrationSettings: (s: IntegrationSettings) => void;
  updateIntegrationSettings: (fn: (prev: IntegrationSettings) => IntegrationSettings) => void;
  setPreferences: (p: AppPreferences) => void;
  updatePreferences: (partial: Partial<AppPreferences>) => void;
  setPublishStage: (s: string) => void;
  setRunners: (r: RunnerInfo[]) => void;
  setSelectedRunner: (id: string) => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  integrationSettings: DEFAULT_INTEGRATION_SETTINGS,
  preferences: DEFAULT_PREFERENCES,
  publishStage: "notebooklm",
  runners: FALLBACK_RUNNERS,
  selectedRunner: "bm",

  setIntegrationSettings: (s) => set({ integrationSettings: s }),
  updateIntegrationSettings: (fn) =>
    set((state) => ({ integrationSettings: fn(state.integrationSettings) })),
  setPreferences: (p) => set({ preferences: p }),
  updatePreferences: (partial) =>
    set((s) => ({ preferences: { ...s.preferences, ...partial } })),
  setPublishStage: (s) => set({ publishStage: s }),
  setRunners: (r) => set({ runners: r }),
  setSelectedRunner: (id) => set({ selectedRunner: id }),
  resetSettings: () =>
    set({
      integrationSettings: DEFAULT_INTEGRATION_SETTINGS,
      preferences: DEFAULT_PREFERENCES,
      publishStage: "notebooklm",
      runners: FALLBACK_RUNNERS,
      selectedRunner: "bm",
    }),
}));
