import { create } from "zustand";
import type { BridgeLog, RunHistoryEntry, RunState } from "../types";

export interface PipelineState {
  runState: RunState;
  bridgeOnline: boolean;
  bridgeLogs: BridgeLog[];
  statusMessage: string;
  dryRunMode: boolean;
  runHistory: RunHistoryEntry[];
  activeRunnerId: string;

  setRunState: (state: RunState) => void;
  setBridgeOnline: (online: boolean) => void;
  appendLogs: (logs: BridgeLog[]) => void;
  pushLocalLog: (level: string, message: string) => void;
  setStatusMessage: (msg: string) => void;
  setDryRunMode: (on: boolean) => void;
  toggleDryRunMode: () => void;
  setRunHistory: (history: RunHistoryEntry[]) => void;
  addRunToHistory: (entry: RunHistoryEntry) => void;
  clearRunHistory: () => void;
  setActiveRunnerId: (id: string) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  runState: "idle",
  bridgeOnline: false,
  bridgeLogs: [],
  statusMessage: "Ready.",
  dryRunMode: false,
  runHistory: [],
  activeRunnerId: "bm",

  setRunState: (state) => set({ runState: state }),
  setBridgeOnline: (online) => set({ bridgeOnline: online }),
  appendLogs: (logs) =>
    set((s) => ({ bridgeLogs: [...s.bridgeLogs.slice(-600), ...logs] })),
  pushLocalLog: (level, message) =>
    set((s) => ({
      bridgeLogs: [
        ...s.bridgeLogs,
        {
          id: Date.now() + Math.floor(Math.random() * 1000),
          ts: new Date().toISOString(),
          level,
          message,
        },
      ],
    })),
  setStatusMessage: (msg) => set({ statusMessage: msg }),
  setDryRunMode: (on) => set({ dryRunMode: on }),
  toggleDryRunMode: () => set((s) => ({ dryRunMode: !s.dryRunMode })),
  setRunHistory: (history) => set({ runHistory: history }),
  addRunToHistory: (entry) =>
    set((s) => ({ runHistory: [entry, ...s.runHistory].slice(0, 50) })),
  clearRunHistory: () => set({ runHistory: [] }),
  setActiveRunnerId: (id) => set({ activeRunnerId: id }),
}));
