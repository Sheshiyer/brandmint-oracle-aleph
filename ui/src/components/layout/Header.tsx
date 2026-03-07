import { useMemo } from "react";
import { usePipelineStore } from "../../stores/pipelineStore";
import { useUiStore } from "../../stores/uiStore";
import { useSettingsStore } from "../../stores/settingsStore";

export default function Header() {
  const bridgeOnline = usePipelineStore((s) => s.bridgeOnline);
  const runState = usePipelineStore((s) => s.runState);
  const runHistory = usePipelineStore((s) => s.runHistory);

  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);

  const selectedPageId = useUiStore((s) => s.selectedPageId);
  const processPages = useMemo(() => {
    // We import lazily to avoid circular deps in layout
    const { buildProcessPages } = require("../../lib/utils");
    return buildProcessPages();
  }, []);

  const selectedPage = useMemo(
    () => processPages.find((p: { id: string }) => p.id === selectedPageId) ?? processPages[0],
    [processPages, selectedPageId],
  );

  return (
    <header className="studio-header hud-header">
      <button
        className="sidebar-toggle-btn"
        onClick={toggleSidebar}
        title={sidebarCollapsed ? "Show sidebar" : "Hide sidebar"}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {sidebarCollapsed ? (
            <>
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </>
          ) : (
            <>
              <rect x="3" y="3" width="7" height="18" rx="1" />
              <line x1="14" y1="6" x2="21" y2="6" />
              <line x1="14" y1="12" x2="21" y2="12" />
              <line x1="14" y1="18" x2="21" y2="18" />
            </>
          )}
        </svg>
      </button>
      <div className="header-breadcrumb">
        <strong>Brandmint</strong>
        <span style={{ color: "var(--fg-tertiary)" }}>/</span>
        <strong>{selectedPage?.title}</strong>
      </div>
      <div className="hud-cell-right">
        <span className={`status-pill ${bridgeOnline ? "ok" : "warn"}`}>
          <span className={`status-dot ${bridgeOnline ? "pulse" : "danger"}`} />
          {bridgeOnline ? "online" : "offline"}
        </span>
        <span
          className={`status-pill ${
            runState === "running" || runState === "retrying" ? "ok" : ""
          }`}
        >
          <span
            className={`status-dot ${
              runState === "running" || runState === "retrying" ? "pulse" : ""
            }`}
          />
          {runState}
        </span>
        <button
          className="header-icon-btn"
          onClick={() => setSelectedPageId("process-history")}
          title="Run History"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </button>
        <button
          className="header-icon-btn"
          onClick={() => setSelectedPageId("process-settings")}
          title="Settings (⌘,)"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
          </svg>
        </button>
        <button
          className="btn"
          onClick={() => setCommandPaletteOpen(true)}
          title="Command palette (⌘K)"
        >
          ⌘K
        </button>
      </div>
    </header>
  );
}
