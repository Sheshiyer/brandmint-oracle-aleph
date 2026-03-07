import { type ReactNode, useMemo, useEffect, useRef } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";
import ToastContainer from "../ui/Toast";
import { useUiStore } from "../../stores/uiStore";
import { usePipelineStore } from "../../stores/pipelineStore";
import { useProjectStore } from "../../stores/projectStore";
import { useSettingsStore } from "../../stores/settingsStore";
import { useReferenceStore } from "../../stores/referenceStore";
import { useArtifactStore } from "../../stores/artifactStore";
import { buildProcessPages, waveForPage } from "../../lib/utils";
import { notify, requestNotificationPermission } from "../../lib/notifications";
import { readTextFile } from "../../lib/native";
import { isTauri } from "../../lib/tauri";
import type { BridgeLog, ArtifactItem, ReferenceImage, RunnerInfo, RunState, IntegrationSettings } from "../../types";
import {
  DRAFT_KEY, HISTORY_KEY, PROJECTS_KEY, PREFS_KEY,
  DEFAULT_PREFERENCES, DEFAULT_INTEGRATION_SETTINGS, FALLBACK_RUNNERS,
  emptyExtraction,
} from "../../types";
import { defaultConfigDraft } from "../../lib/utils";

interface ShellProps {
  children: ReactNode;
}

export default function Shell({ children }: ShellProps) {
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);
  const sidebarWidth = useUiStore((s) => s.sidebarWidth);
  const setSidebarWidth = useUiStore((s) => s.setSidebarWidth);
  const isResizingSidebar = useUiStore((s) => s.isResizingSidebar);
  const setIsResizingSidebar = useUiStore((s) => s.setIsResizingSidebar);
  const isDraggingOver = useUiStore((s) => s.isDraggingOver);
  const setIsDraggingOver = useUiStore((s) => s.setIsDraggingOver);
  const commandPaletteOpen = useUiStore((s) => s.commandPaletteOpen);
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen);
  const commandQuery = useUiStore((s) => s.commandQuery);
  const setCommandQuery = useUiStore((s) => s.setCommandQuery);
  const contextMenu = useUiStore((s) => s.contextMenu);
  const setContextMenu = useUiStore((s) => s.setContextMenu);
  const selectedPageId = useUiStore((s) => s.selectedPageId);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);
  const bumpPageTransition = useUiStore((s) => s.bumpPageTransition);
  const pageTransitionKey = useUiStore((s) => s.pageTransitionKey);
  const addToast = useUiStore((s) => s.addToast);

  const runState = usePipelineStore((s) => s.runState);
  const setRunState = usePipelineStore((s) => s.setRunState);
  const bridgeOnline = usePipelineStore((s) => s.bridgeOnline);
  const setBridgeOnline = usePipelineStore((s) => s.setBridgeOnline);
  const bridgeLogs = usePipelineStore((s) => s.bridgeLogs);
  const appendLogs = usePipelineStore((s) => s.appendLogs);
  const pushLocalLog = usePipelineStore((s) => s.pushLocalLog);
  const statusMessage = usePipelineStore((s) => s.statusMessage);
  const setStatusMessage = usePipelineStore((s) => s.setStatusMessage);
  const dryRunMode = usePipelineStore((s) => s.dryRunMode);
  const setRunHistory = usePipelineStore((s) => s.setRunHistory);
  const addRunToHistory = usePipelineStore((s) => s.addRunToHistory);
  const setActiveRunnerId = usePipelineStore((s) => s.setActiveRunnerId);

  const projectName = useProjectStore((s) => s.projectName);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const brandFolder = useProjectStore((s) => s.brandFolder);
  const setBrandFolder = useProjectStore((s) => s.setBrandFolder);
  const scenario = useProjectStore((s) => s.scenario);
  const setScenario = useProjectStore((s) => s.setScenario);
  const waves = useProjectStore((s) => s.waves);
  const setWaves = useProjectStore((s) => s.setWaves);
  const configPath = useProjectStore((s) => s.configPath);
  const setConfigPath = useProjectStore((s) => s.setConfigPath);
  const productMdPath = useProjectStore((s) => s.productMdPath);
  const setProductMdPath = useProjectStore((s) => s.setProductMdPath);
  const productMdText = useProjectStore((s) => s.productMdText);
  const setProductMdText = useProjectStore((s) => s.setProductMdText);
  const extraction = useProjectStore((s) => s.extraction);
  const setExtraction = useProjectStore((s) => s.setExtraction);
  const extractionConfirmed = useProjectStore((s) => s.extractionConfirmed);
  const setExtractionConfirmed = useProjectStore((s) => s.setExtractionConfirmed);
  const wizardStep = useProjectStore((s) => s.wizardStep);
  const setWizardStep = useProjectStore((s) => s.setWizardStep);
  const configDraft = useProjectStore((s) => s.configDraft);
  const setConfigDraft = useProjectStore((s) => s.setConfigDraft);
  const exportedAt = useProjectStore((s) => s.exportedAt);
  const setExportedAt = useProjectStore((s) => s.setExportedAt);
  const setLastSavedAt = useProjectStore((s) => s.setLastSavedAt);
  const selectedReferenceIds = useReferenceStore((s) => s.selectedReferenceIds);
  const setSelectedReferenceIds = useReferenceStore((s) => s.setSelectedReferenceIds);
  const setReferences = useReferenceStore((s) => s.setReferences);
  const setReferencesLoading = useReferenceStore((s) => s.setReferencesLoading);
  const setArtifacts = useArtifactStore((s) => s.setArtifacts);

  const publishStage = useSettingsStore((s) => s.publishStage);
  const setPublishStage = useProjectStore((s) => s.setWaves); // reuse setter pattern
  const setIntegrationSettings = useSettingsStore((s) => s.setIntegrationSettings);
  const setRunners = useSettingsStore((s) => s.setRunners);
  const setSelectedRunner = useSettingsStore((s) => s.setSelectedRunner);
  const integrationSettings = useSettingsStore((s) => s.integrationSettings);
  const preferences = useSettingsStore((s) => s.preferences);
  const setPreferences = useSettingsStore((s) => s.setPreferences);

  const wikiHandoffDone = useProjectStore((s) => s.wikiHandoffDone);
  const setWikiHandoffDone = useProjectStore((s) => s.setWikiHandoffDone);
  const astroHandoffDone = useProjectStore((s) => s.astroHandoffDone);
  const setAstroHandoffDone = useProjectStore((s) => s.setAstroHandoffDone);
  const recentProjects = useProjectStore((s) => s.recentProjects);
  const setRecentProjects = useProjectStore((s) => s.setRecentProjects);

  const processPages = useMemo(() => buildProcessPages(), []);
  const selectedPage = useMemo(
    () => processPages.find((p) => p.id === selectedPageId) ?? processPages[0],
    [processPages, selectedPageId],
  );
  const selectedPageIndex = useMemo(
    () => Math.max(0, processPages.findIndex((p) => p.id === selectedPage?.id)),
    [processPages, selectedPage?.id],
  );

  const lastLogIdRef = useRef(0);
  const runStartTimeRef = useRef<number | null>(null);
  const prevRunStateRef = useRef<RunState>("idle");
  const prevBridgeOnlineRef = useRef(true);

  // ── Request notification permission on mount ──
  useEffect(() => {
    void requestNotificationPermission();
  }, []);

  // ── Progress summary for footer ──
  const progressSummary = useMemo(() => {
    // simplified for footer
    const total = processPages.length;
    const done = Math.round(total * 0.15); // placeholder
    return { done, percent: total ? Math.round((done / total) * 100) : 0, attention: 0 };
  }, [processPages.length]);

  // ── Keyboard shortcuts ──
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const inField = Boolean(
        target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT"),
      );

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key === ",") {
        event.preventDefault();
        setSelectedPageId("process-settings");
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "[") {
        event.preventDefault();
        if (selectedPageIndex > 0) setSelectedPageId(processPages[selectedPageIndex - 1].id);
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "]") {
        event.preventDefault();
        if (selectedPageIndex < processPages.length - 1) setSelectedPageId(processPages[selectedPageIndex + 1].id);
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "b") {
        event.preventDefault();
        useUiStore.getState().toggleSidebar();
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "r") {
        event.preventDefault();
        addToast("Refreshing data…", "info");
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "w") {
        event.preventDefault();
        (async () => {
          try {
            const { getCurrentWindow } = await import("@tauri-apps/api/window");
            getCurrentWindow().close();
          } catch { /* browser fallback */ }
        })();
        return;
      }
      if (event.key === "Escape") {
        setCommandPaletteOpen(false);
        return;
      }
      if (inField || commandPaletteOpen) return;

      if (event.key === "ArrowUp" && selectedPageIndex > 0) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex - 1].id);
      }
      if (event.key === "ArrowDown" && selectedPageIndex < processPages.length - 1) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex + 1].id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [commandPaletteOpen, processPages, selectedPageIndex]);

  // ── Sidebar resize ──
  useEffect(() => {
    if (!isResizingSidebar) return;
    const onMove = (e: MouseEvent) => {
      setSidebarWidth(Math.max(200, Math.min(500, e.clientX)));
    };
    const onUp = () => {
      setIsResizingSidebar(false);
      try {
        window.localStorage.setItem("brandmint-sidebar-width", String(sidebarWidth));
      } catch { /* noop */ }
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizingSidebar, sidebarWidth]);

  // ── Context menu dismiss ──
  useEffect(() => {
    if (!contextMenu) return;
    const dismiss = () => setContextMenu(null);
    window.addEventListener("click", dismiss);
    window.addEventListener("contextmenu", dismiss);
    return () => {
      window.removeEventListener("click", dismiss);
      window.removeEventListener("contextmenu", dismiss);
    };
  }, [contextMenu]);

  // ── Command palette reset ──
  useEffect(() => {
    if (!commandPaletteOpen) setCommandQuery("");
  }, [commandPaletteOpen]);

  // ── Page transition ──
  useEffect(() => {
    bumpPageTransition();
  }, [selectedPageId]);

  // ── Draft restore ──
  useEffect(() => {
    const raw = window.localStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed.projectName) setProjectName(parsed.projectName);
      if (parsed.brandFolder) setBrandFolder(parsed.brandFolder);
      if (parsed.scenario) setScenario(parsed.scenario);
      if (parsed.waves) setWaves(parsed.waves);
      if (parsed.configPath) setConfigPath(parsed.configPath);
      if (parsed.productMdPath) setProductMdPath(parsed.productMdPath);
      if (parsed.productMdText) setProductMdText(parsed.productMdText);
      if (parsed.extraction) setExtraction({ ...emptyExtraction, ...parsed.extraction });
      if (typeof parsed.extractionConfirmed === "boolean") setExtractionConfirmed(parsed.extractionConfirmed);
      if (typeof parsed.wizardStep === "number") setWizardStep(Math.max(0, Math.min(4, parsed.wizardStep)));
      if (parsed.configDraft) setConfigDraft(parsed.configDraft);
      if (parsed.selectedReferenceIds) setSelectedReferenceIds(parsed.selectedReferenceIds);
      if (parsed.selectedPageId) setSelectedPageId(parsed.selectedPageId);
      if (parsed.exportedAt) setExportedAt(parsed.exportedAt);
      if (parsed.dryRunMode) usePipelineStore.getState().setDryRunMode(Boolean(parsed.dryRunMode));
      if (typeof parsed.wikiHandoffDone === "boolean") setWikiHandoffDone(parsed.wikiHandoffDone);
      if (typeof parsed.astroHandoffDone === "boolean") setAstroHandoffDone(parsed.astroHandoffDone);
      setStatusMessage("Draft restored.");
    } catch {
      setStatusMessage("Draft was invalid. Starting fresh.");
    }
  }, []);

  // ── Load history/projects/preferences ──
  useEffect(() => {
    try {
      const h = localStorage.getItem(HISTORY_KEY);
      if (h) setRunHistory(JSON.parse(h));
    } catch { /* noop */ }
    try {
      const p = localStorage.getItem(PROJECTS_KEY);
      if (p) setRecentProjects(JSON.parse(p));
    } catch { /* noop */ }
    try {
      const pr = localStorage.getItem(PREFS_KEY);
      if (pr) setPreferences({ ...DEFAULT_PREFERENCES, ...JSON.parse(pr) });
    } catch { /* noop */ }
  }, []);

  // ── Save preferences ──
  useEffect(() => {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(preferences));
    } catch { /* noop */ }
  }, [preferences]);

  // ── Auto-save draft ──
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        const payload = {
          projectName, brandFolder, scenario, waves, configPath, productMdPath, productMdText,
          extraction, extractionConfirmed, wizardStep, configDraft, selectedReferenceIds,
          selectedPageId, exportedAt, dryRunMode, wikiHandoffDone, astroHandoffDone,
        };
        window.localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
        setLastSavedAt(new Date().toLocaleTimeString());
      } catch { /* noop */ }
    }, 1500);
    return () => clearTimeout(timer);
  }, [
    configDraft, brandFolder, configPath, dryRunMode, exportedAt, extraction,
    extractionConfirmed, productMdPath, productMdText, projectName, scenario,
    selectedPageId, selectedReferenceIds, waves, wizardStep, wikiHandoffDone, astroHandoffDone,
  ]);

  // ── Bridge polling ──
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const stateRes = await fetch("/api/state");
        if (stateRes.ok) {
          const state = await stateRes.json();
          setBridgeOnline(true);
          if (["idle", "running", "retrying", "aborted"].includes(state.state)) {
            setRunState(state.state as RunState);
          }
          if (state.runner) setActiveRunnerId(String(state.runner));
        } else {
          setBridgeOnline(false);
        }
        const logsRes = await fetch(`/api/logs?since=${lastLogIdRef.current}`);
        if (logsRes.ok) {
          const data = await logsRes.json();
          const incoming: BridgeLog[] = data.logs || [];
          if (incoming.length > 0) {
            appendLogs(incoming);
            lastLogIdRef.current = incoming[incoming.length - 1].id;
          }
        }
      } catch {
        setBridgeOnline(false);
      }
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  // ── Artifact polling ──
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/artifacts?limit=400");
        if (!res.ok) return;
        const data = await res.json();
        setArtifacts((data.artifacts || []) as ArtifactItem[]);
      } catch { /* noop */ }
    };
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  // ── References ──
  useEffect(() => {
    (async () => {
      setReferencesLoading(true);
      try {
        const res = await fetch("/api/references?limit=1000");
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();
        setReferences((data.references || []) as ReferenceImage[]);
      } catch {
        pushLocalLog("error", "Unable to load references.");
      } finally {
        setReferencesLoading(false);
      }
    })();
  }, []);

  // ── Integration settings ──
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/settings");
        if (!res.ok) return;
        const data = await res.json();
        const next = data.settings as IntegrationSettings | undefined;
        if (next) {
          setIntegrationSettings({
            openrouter: { ...DEFAULT_INTEGRATION_SETTINGS.openrouter, ...(next.openrouter || {}) },
            nbrain: { ...DEFAULT_INTEGRATION_SETTINGS.nbrain, ...(next.nbrain || {}) },
            defaults: { ...DEFAULT_INTEGRATION_SETTINGS.defaults, ...(next.defaults || {}) },
          });
          if (next.defaults?.preferredRunner) {
            setSelectedRunner(next.defaults.preferredRunner);
          }
        }
      } catch {
        pushLocalLog("warn", "Unable to load provider settings.");
      }
    })();
  }, []);

  // ── Runners ──
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/runners");
        if (!res.ok) return;
        const data = await res.json();
        const catalog = (data.runners || []) as RunnerInfo[];
        if (catalog.length) {
          setRunners(catalog);
        } else {
          setRunners(FALLBACK_RUNNERS);
        }
      } catch {
        setRunners(FALLBACK_RUNNERS);
      }
    })();
  }, [integrationSettings.defaults.preferredRunner]);

  // ── Run state notifications ──
  useEffect(() => {
    const prev = prevRunStateRef.current;
    prevRunStateRef.current = runState;
    if (prev === "running" && runState === "idle") {
      addToast("Pipeline run completed", "success");
      void notify("Pipeline Complete", "Brand generation finished successfully");
    } else if (prev === "running" && runState === "aborted") {
      addToast("Pipeline run aborted", "error");
      void notify("Pipeline Aborted", "The pipeline run was aborted");
    } else if (runState === "running" && prev !== "running") {
      runStartTimeRef.current = Date.now();
    }
  }, [runState]);

  // ── Bridge offline notifications ──
  useEffect(() => {
    if (prevBridgeOnlineRef.current && !bridgeOnline) {
      addToast("Bridge disconnected", "error");
      void notify("Sidecar Error", "Bridge process crashed — restart from settings");
    } else if (!prevBridgeOnlineRef.current && bridgeOnline) {
      addToast("Bridge reconnected", "success");
    }
    prevBridgeOnlineRef.current = bridgeOnline;
  }, [bridgeOnline]);

  // ── Drag & Drop ──
  useEffect(() => {
    const onDragOver = (e: DragEvent) => { e.preventDefault(); setIsDraggingOver(true); };
    const onDragLeave = (e: DragEvent) => {
      if (e.relatedTarget === null || !(e.currentTarget as Node)?.contains(e.relatedTarget as Node)) {
        setIsDraggingOver(false);
      }
    };
    const onDrop = (e: DragEvent) => {
      e.preventDefault();
      setIsDraggingOver(false);
      const files = e.dataTransfer?.files;
      if (!files?.length) return;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const name = file.name.toLowerCase();

        // Attempt to get the full native path (Tauri provides this on some platforms)
        const nativePath = (file as File & { path?: string }).path;

        if (name.endsWith(".yaml") || name.endsWith(".yml")) {
          if (nativePath && isTauri()) {
            // In Tauri, set the full native path so the sidecar can find the config
            setConfigPath(nativePath);
            addToast(`Loaded config: ${file.name}`, "success");
          } else {
            file.text().then(() => {
              setConfigPath(file.name);
              addToast(`Loaded config: ${file.name}`, "success");
            });
          }
        } else if (name.endsWith(".md")) {
          if (nativePath && isTauri()) {
            // In Tauri, read the file content via native FS for the full path
            setProductMdPath(nativePath);
            readTextFile(nativePath).then((text) => {
              setProductMdText(text);
              addToast(`Loaded product doc: ${file.name}`, "success");
            }).catch(() => {
              // Fallback to browser File API
              file.text().then((text) => {
                setProductMdText(text);
                addToast(`Loaded product doc: ${file.name}`, "success");
              });
            });
          } else {
            file.text().then((text) => {
              setProductMdText(text);
              setProductMdPath(file.name);
              addToast(`Loaded product doc: ${file.name}`, "success");
            });
          }
        } else if (file.type === "" && file.size === 0 && nativePath) {
          // Likely a folder drop (size 0, no type) — set as brand folder
          setBrandFolder(nativePath);
          addToast(`Brand folder: ${file.name}`, "success");
        }
      }

      // Also check for Tauri file-drop paths in dataTransfer items
      const tauriPaths = e.dataTransfer?.getData("text/uri-list");
      if (tauriPaths) {
        const paths = tauriPaths.split("\n").map((p) => p.trim()).filter(Boolean);
        for (const p of paths) {
          const lower = p.toLowerCase();
          if (lower.endsWith(".yaml") || lower.endsWith(".yml")) {
            setConfigPath(p);
            addToast(`Config path: ${p.split("/").pop()}`, "success");
          } else if (lower.endsWith(".md")) {
            setProductMdPath(p);
            if (isTauri()) {
              readTextFile(p).then((text) => {
                setProductMdText(text);
                addToast(`Product doc: ${p.split("/").pop()}`, "success");
              }).catch(() => {});
            }
          } else if (!lower.includes(".")) {
            // No extension — likely a folder path
            setBrandFolder(p);
            addToast(`Brand folder: ${p.split("/").pop()}`, "success");
          }
        }
      }
    };
    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, []);

  // ── Command actions ──
  const commandActions = useMemo(() => {
    const pageActions = processPages.map((page, index) => ({
      id: `goto-${page.id}`,
      label: `Go to: ${page.title}`,
      hint: `Page ${index + 1}`,
      run: () => {
        setSelectedPageId(page.id);
        setCommandPaletteOpen(false);
      },
    }));
    return [
      { id: "open-settings", label: "Open Provider Settings", hint: "Open model/API config", run: () => { setSelectedPageId("process-settings"); setCommandPaletteOpen(false); } },
      ...pageActions,
    ];
  }, [processPages]);

  const filteredCommandActions = useMemo(() => {
    const needle = commandQuery.trim().toLowerCase();
    if (!needle) return commandActions.slice(0, 14);
    return commandActions.filter((a) => `${a.label} ${a.hint || ""}`.toLowerCase().includes(needle)).slice(0, 20);
  }, [commandActions, commandQuery]);

  return (
    <div className="studio-shell frame-shell">
      <Header />

      <div
        className={`studio-grid ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}
        style={!sidebarCollapsed ? ({ gridTemplateColumns: `${sidebarWidth}px 1fr` } as React.CSSProperties) : undefined}
      >
        <Sidebar />

        <main className="process-content">
          <section className="page-hero">
            <p className="page-index">
              {selectedPage ? waveForPage(selectedPage).label : ""} &middot; Page {selectedPageIndex + 1} of{" "}
              {processPages.length}
            </p>
            <h2>{selectedPage?.title}</h2>
            <p>{selectedPage?.objective}</p>
            <div className="chip-row" style={{ marginTop: 8 }}>
              {selectedPage?.focus.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </section>

          <div key={pageTransitionKey} className="content-main-layout page-transition-enter page-transition-active">
            {!bridgeOnline && selectedPage?.kind !== "settings" && selectedPage?.kind !== "history" ? (
              <div style={{ padding: 24 }}>
                <div className="skeleton skeleton-block" />
                <div className="skeleton skeleton-line" style={{ width: "80%" }} />
                <div className="skeleton skeleton-line" style={{ width: "55%" }} />
                <div className="skeleton skeleton-line" />
                <div className="skeleton skeleton-block" style={{ marginTop: 16 }} />
              </div>
            ) : (
              children
            )}
          </div>
        </main>
      </div>

      <footer className="studio-footer">
        <span>{statusMessage}</span>
        <span>{projectName}</span>
        <span>{scenario}</span>
        <span>{progressSummary.percent}% complete</span>
      </footer>

      {/* Command Palette */}
      {commandPaletteOpen && (
        <div className="command-palette-overlay" onClick={() => setCommandPaletteOpen(false)}>
          <div className="command-palette" onClick={(event) => event.stopPropagation()}>
            <input
              autoFocus
              value={commandQuery}
              onChange={(e) => setCommandQuery(e.target.value)}
              placeholder="Run action or jump to page…"
            />
            <div className="command-list">
              {filteredCommandActions.map((action) => (
                <button key={action.id} className="command-item" onClick={action.run}>
                  <strong>{action.label}</strong>
                  {action.hint && <span>{action.hint}</span>}
                </button>
              ))}
              {!filteredCommandActions.length && <p className="command-empty">No matching commands.</p>}
            </div>
          </div>
        </div>
      )}

      <ToastContainer />

      {/* Drag-drop overlay */}
      {isDraggingOver && (
        <div className="drop-overlay">
          <div className="drop-overlay-inner">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>Drop files or folders to load</p>
            <small>.yaml &middot; .md &middot; folder</small>
          </div>
        </div>
      )}

      {/* Context menu */}
      {contextMenu &&
        (() => {
          const ctxPage = processPages.find((p) => p.id === contextMenu.pageId);
          return (
            <div className="context-menu" style={{ left: contextMenu.x, top: contextMenu.y }}>
              <button
                className="context-menu-item"
                onClick={() => {
                  if (ctxPage) setSelectedPageId(ctxPage.id);
                  setContextMenu(null);
                }}
              >
                Open <small>Enter</small>
              </button>
              <button
                className="context-menu-item"
                onClick={() => {
                  if (ctxPage) navigator.clipboard.writeText(ctxPage.title);
                  setContextMenu(null);
                  addToast("Copied title", "info");
                }}
              >
                Copy title <small>⌘C</small>
              </button>
              <div className="context-menu-divider" />
              <button
                className="context-menu-item"
                onClick={() => {
                  setContextMenu(null);
                }}
              >
                Mark done
              </button>
            </div>
          );
        })()}
    </div>
  );
}
