import { create } from "zustand";
import type { PageKind, Toast } from "../types";

export interface UiState {
  activePage: PageKind;
  selectedPageId: string;
  toasts: Toast[];
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;
  commandQuery: string;
  pageSearch: string;
  collapsedWaves: Record<string, boolean>;
  pageTransitionKey: number;
  isDraggingOver: boolean;
  isResizingSidebar: boolean;
  sidebarWidth: number;
  contextMenu: { x: number; y: number; pageId: string } | null;

  setActivePage: (p: PageKind) => void;
  setSelectedPageId: (id: string) => void;
  addToast: (message: string, kind: Toast["kind"]) => void;
  dismissToast: (id: number) => void;
  removeToast: (id: number) => void;
  setSidebarCollapsed: (c: boolean) => void;
  toggleSidebar: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setCommandQuery: (q: string) => void;
  setPageSearch: (q: string) => void;
  setCollapsedWaves: (fn: (prev: Record<string, boolean>) => Record<string, boolean>) => void;
  bumpPageTransition: () => void;
  setIsDraggingOver: (d: boolean) => void;
  setIsResizingSidebar: (r: boolean) => void;
  setSidebarWidth: (w: number) => void;
  setContextMenu: (m: { x: number; y: number; pageId: string } | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activePage: "journey",
  selectedPageId: "journey-01",
  toasts: [],
  sidebarCollapsed: false,
  commandPaletteOpen: false,
  commandQuery: "",
  pageSearch: "",
  collapsedWaves: {
    "wave-1": false,
    "wave-2": false,
    "wave-3": false,
    "wave-4": false,
    "wave-5": false,
    "wave-6": false,
    "wave-7": false,
    "wave-8": false,
    "wave-app": false,
    "wave-x": false,
  },
  pageTransitionKey: 0,
  isDraggingOver: false,
  isResizingSidebar: false,
  sidebarWidth: (() => {
    try {
      return Number(window.localStorage.getItem("brandmint-sidebar-width")) || 280;
    } catch {
      return 280;
    }
  })(),
  contextMenu: null,

  setActivePage: (p) => set({ activePage: p }),
  setSelectedPageId: (id) => set({ selectedPageId: id }),
  addToast: (message, kind) => {
    const id = Date.now() + Math.floor(Math.random() * 10000);
    set((s) => ({ toasts: [...s.toasts.slice(-4), { id, message, kind }] }));
    setTimeout(() => {
      set((s) => ({
        toasts: s.toasts.map((t) => (t.id === id ? { ...t, exiting: true } : t)),
      }));
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 220);
    }, 3500);
  },
  dismissToast: (id) => {
    set((s) => ({
      toasts: s.toasts.map((t) => (t.id === id ? { ...t, exiting: true } : t)),
    }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 220);
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  setSidebarCollapsed: (c) => set({ sidebarCollapsed: c }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setCommandQuery: (q) => set({ commandQuery: q }),
  setPageSearch: (q) => set({ pageSearch: q }),
  setCollapsedWaves: (fn) => set((s) => ({ collapsedWaves: fn(s.collapsedWaves) })),
  bumpPageTransition: () => set((s) => ({ pageTransitionKey: s.pageTransitionKey + 1 })),
  setIsDraggingOver: (d) => set({ isDraggingOver: d }),
  setIsResizingSidebar: (r) => set({ isResizingSidebar: r }),
  setSidebarWidth: (w) => set({ sidebarWidth: w }),
  setContextMenu: (m) => set({ contextMenu: m }),
}));
