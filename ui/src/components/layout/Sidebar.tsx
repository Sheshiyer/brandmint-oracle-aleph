import { useMemo } from "react";
import { useUiStore } from "../../stores/uiStore";
import { useProjectStore } from "../../stores/projectStore";
import { buildProcessPages, waveForPage, groupPagesByWave } from "../../lib/utils";
import type { PageStatus, ProcessPage } from "../../types";
import { usePipelineStore } from "../../stores/pipelineStore";
import { useReferenceStore } from "../../stores/referenceStore";
import { useArtifactStore } from "../../stores/artifactStore";
import { useSettingsStore } from "../../stores/settingsStore";

export default function Sidebar() {
  const selectedPageId = useUiStore((s) => s.selectedPageId);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);
  const pageSearch = useUiStore((s) => s.pageSearch);
  const setPageSearch = useUiStore((s) => s.setPageSearch);
  const collapsedWaves = useUiStore((s) => s.collapsedWaves);
  const setCollapsedWaves = useUiStore((s) => s.setCollapsedWaves);
  const isResizingSidebar = useUiStore((s) => s.isResizingSidebar);
  const setIsResizingSidebar = useUiStore((s) => s.setIsResizingSidebar);
  const setContextMenu = useUiStore((s) => s.setContextMenu);
  const addToast = useUiStore((s) => s.addToast);

  const recentProjects = useProjectStore((s) => s.recentProjects);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const setConfigPath = useProjectStore((s) => s.setConfigPath);
  const setScenario = useProjectStore((s) => s.setScenario);
  const setBrandFolder = useProjectStore((s) => s.setBrandFolder);
  const productMdText = useProjectStore((s) => s.productMdText);
  const extractionConfirmed = useProjectStore((s) => s.extractionConfirmed);
  const wizardStep = useProjectStore((s) => s.wizardStep);
  const exportedAt = useProjectStore((s) => s.exportedAt);
  const extraction = useProjectStore((s) => s.extraction);
  const wikiHandoffDone = useProjectStore((s) => s.wikiHandoffDone);
  const astroHandoffDone = useProjectStore((s) => s.astroHandoffDone);

  const runState = usePipelineStore((s) => s.runState);
  const bridgeLogs = usePipelineStore((s) => s.bridgeLogs);
  const activeRunnerId = usePipelineStore((s) => s.activeRunnerId);
  const runHistory = usePipelineStore((s) => s.runHistory);

  const selectedReferenceIds = useReferenceStore((s) => s.selectedReferenceIds);
  const references = useReferenceStore((s) => s.references);

  const artifacts = useArtifactStore((s) => s.artifacts);

  const integrationSettings = useSettingsStore((s) => s.integrationSettings);
  const selectedRunner = useSettingsStore((s) => s.selectedRunner);
  const runners = useSettingsStore((s) => s.runners);

  const processPages = useMemo(() => buildProcessPages(), []);

  const selectedPage = useMemo(
    () => processPages.find((p) => p.id === selectedPageId) ?? processPages[0],
    [processPages, selectedPageId],
  );

  const selectedPageIndex = useMemo(
    () => Math.max(0, processPages.findIndex((p) => p.id === selectedPage?.id)),
    [processPages, selectedPage?.id],
  );

  const hasExtraction = Boolean(
    extraction.productName || extraction.audience || extraction.valueProposition || extraction.differentiators,
  );

  // Page status map
  const pageStatusMap = useMemo<Record<string, PageStatus>>(() => {
    const map: Record<string, PageStatus> = {};
    const errorCount = bridgeLogs.filter((r) => r.level === "error").length;
    for (const page of processPages) {
      let status: PageStatus =
        processPages.findIndex((r) => r.id === page.id) < selectedPageIndex ? "done" : "pending";
      if (page.id === selectedPage?.id) {
        status = "active";
      } else if (page.kind === "intake") {
        status = productMdText.trim().length > 80 ? "done" : "pending";
      } else if (page.kind === "extraction") {
        status = extractionConfirmed ? "done" : hasExtraction ? "active" : "pending";
      } else if (page.kind === "wizard") {
        status = extractionConfirmed && wizardStep >= 4 ? "done" : extractionConfirmed ? "active" : "pending";
      } else if (page.kind === "export") {
        status = exportedAt ? "done" : "pending";
      } else if (page.kind === "launch") {
        status = runState === "running" || runState === "retrying" ? "active" : exportedAt ? "done" : "pending";
      } else if (page.kind === "activity") {
        status = bridgeLogs.length ? "done" : "pending";
      } else if (page.kind === "triage") {
        status = errorCount > 0 ? "attention" : "done";
      } else if (page.kind === "settings") {
        status = integrationSettings.openrouter.hasApiKey ? "done" : "attention";
      } else if (page.kind === "reference-curation") {
        status = selectedReferenceIds.length >= 6 ? "done" : references.length ? "active" : "pending";
      } else if (page.kind === "reference-library") {
        status = references.length ? "done" : "pending";
      } else if (page.kind === "fal-dry-run") {
        status = artifacts.some((r) => r.relativePath.includes("simulated/generated")) ? "done" : "pending";
      } else if (page.kind === "runner-workbench") {
        status = selectedRunner ? "active" : "pending";
      } else if (page.kind === "runner-matrix") {
        status = runners.length ? "done" : "pending";
      } else if (page.kind === "artifacts") {
        status = artifacts.length ? "done" : "pending";
      } else if (page.kind === "handoff") {
        status = exportedAt && selectedReferenceIds.length ? "done" : "pending";
      } else if (page.kind === "publish-notebooklm") {
        const hasNotebookLog = bridgeLogs.some((r) => r.message.toLowerCase().includes("publish:notebooklm"));
        status =
          activeRunnerId === "publish:notebooklm" && (runState === "running" || runState === "retrying")
            ? "active"
            : hasNotebookLog
              ? "done"
              : "pending";
      } else if (page.kind === "wiki-handoff") {
        status = wikiHandoffDone ? "done" : "pending";
      } else if (page.kind === "astro-build") {
        status = astroHandoffDone ? "done" : "pending";
      } else if (page.kind === "history") {
        status = runHistory.length ? "done" : "pending";
      } else if (page.kind === "output-viewer") {
        status = artifacts.length ? "done" : "pending";
      }
      map[page.id] = status;
    }
    return map;
  }, [
    artifacts, bridgeLogs, exportedAt, extractionConfirmed, hasExtraction, processPages,
    productMdText, references.length, runState, runners.length,
    integrationSettings.openrouter.hasApiKey, activeRunnerId, selectedPage?.id,
    selectedPageIndex, selectedReferenceIds.length, selectedRunner, wikiHandoffDone,
    astroHandoffDone, wizardStep, runHistory.length,
  ]);

  const filteredPages = useMemo(() => {
    const needle = pageSearch.trim().toLowerCase();
    if (!needle) return processPages;
    return processPages.filter(
      (page) =>
        page.title.toLowerCase().includes(needle) ||
        page.track.toLowerCase().includes(needle) ||
        page.objective.toLowerCase().includes(needle),
    );
  }, [pageSearch, processPages]);

  const waveGroups = useMemo(() => groupPagesByWave(filteredPages), [filteredPages]);

  return (
    <aside className="process-sidebar" style={{ position: "relative" }}>
      <div
        className={`sidebar-resize-handle${isResizingSidebar ? " dragging" : ""}`}
        onMouseDown={() => setIsResizingSidebar(true)}
      />

      {/* Quick-access app section */}
      <div className="sidebar-quick-access">
        <button
          className={`quick-access-btn${selectedPage?.kind === "settings" ? " active" : ""}`}
          onClick={() => setSelectedPageId("process-settings")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
          </svg>
          Settings
        </button>
        <button
          className={`quick-access-btn${selectedPage?.kind === "history" ? " active" : ""}`}
          onClick={() => setSelectedPageId("process-history")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          History
        </button>
        <button
          className={`quick-access-btn${selectedPage?.kind === "output-viewer" ? " active" : ""}`}
          onClick={() => setSelectedPageId("process-output-viewer")}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          Outputs
        </button>
      </div>

      {recentProjects.length > 0 && (
        <div className="sidebar-recent-projects">
          <small className="sidebar-section-label">Recent Projects</small>
          {recentProjects.slice(0, 3).map((proj) => (
            <button
              key={proj.path}
              className="quick-access-btn project-btn"
              onClick={() => {
                setBrandFolder(proj.path);
                setProjectName(proj.name);
                setScenario(proj.scenario);
                addToast(`Loaded project: ${proj.name}`, "info");
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
              </svg>
              <span>{proj.name}</span>
              <small>{proj.scenario}</small>
            </button>
          ))}
        </div>
      )}

      <label className="field">
        Find page
        <input value={pageSearch} onChange={(e) => setPageSearch(e.target.value)} placeholder="search page, track, objective" />
      </label>

      {waveGroups.map((wave) => {
        const done = wave.pages.filter((page) => pageStatusMap[page.id] === "done").length;
        const attention = wave.pages.filter((page) => pageStatusMap[page.id] === "attention").length;
        const percent = wave.pages.length ? Math.round((done / wave.pages.length) * 100) : 0;
        return (
          <section key={wave.id} className="wave-section">
            <button
              className="wave-toggle"
              onClick={() => setCollapsedWaves((prev) => ({ ...prev, [wave.id]: !prev[wave.id] }))}
            >
              <div className="wave-topline">
                <h3>{wave.label}</h3>
                <span>
                  {done}/{wave.pages.length} done
                </span>
                <em className={`wave-caret ${collapsedWaves[wave.id] ? "collapsed" : ""}`}>▾</em>
              </div>
              <div className="wave-progress-row">
                <div className="wave-progress-track" aria-hidden="true">
                  <div className="wave-progress-fill" style={{ width: `${percent}%` }} />
                </div>
                <span>{attention > 0 ? `${attention} attention` : `${percent}%`}</span>
              </div>
            </button>
            {!collapsedWaves[wave.id] && (
              <div className="sidebar-pages">
                {wave.pages.map((page) => (
                  <button
                    key={page.id}
                    className={`page-link ${page.id === selectedPage?.id ? "active" : ""}`}
                    onClick={() => setSelectedPageId(page.id)}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      setContextMenu({
                        x: Math.min(e.clientX, window.innerWidth - 180),
                        y: Math.min(e.clientY, window.innerHeight - 120),
                        pageId: page.id,
                      });
                    }}
                  >
                    <span>{processPages.findIndex((r) => r.id === page.id) + 1}</span>
                    <div>
                      <strong>{page.title}</strong>
                      <small>{page.objective}</small>
                    </div>
                    <em className={`dot ${pageStatusMap[page.id] || "pending"}`} />
                  </button>
                ))}
              </div>
            )}
          </section>
        );
      })}
    </aside>
  );
}
