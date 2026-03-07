import { useMemo, useState } from "react";
import { usePipelineStore } from "../stores/pipelineStore";
import { useProjectStore } from "../stores/projectStore";
import { useSettingsStore } from "../stores/settingsStore";
import { useUiStore } from "../stores/uiStore";
import { buildProcessPages } from "../lib/utils";
import { pickYamlFile, pickFolder } from "../lib/native";
import type { PageStatus } from "../types";

export default function LaunchPage() {
  const runState = usePipelineStore((s) => s.runState);
  const setRunState = usePipelineStore((s) => s.setRunState);
  const bridgeOnline = usePipelineStore((s) => s.bridgeOnline);
  const bridgeLogs = usePipelineStore((s) => s.bridgeLogs);
  const pushLocalLog = usePipelineStore((s) => s.pushLocalLog);
  const statusMessage = usePipelineStore((s) => s.statusMessage);
  const setStatusMessage = usePipelineStore((s) => s.setStatusMessage);
  const dryRunMode = usePipelineStore((s) => s.dryRunMode);

  const scenario = useProjectStore((s) => s.scenario);
  const setScenario = useProjectStore((s) => s.setScenario);
  const waves = useProjectStore((s) => s.waves);
  const setWaves = useProjectStore((s) => s.setWaves);
  const configPath = useProjectStore((s) => s.configPath);
  const setConfigPath = useProjectStore((s) => s.setConfigPath);
  const brandFolder = useProjectStore((s) => s.brandFolder);
  const setBrandFolder = useProjectStore((s) => s.setBrandFolder);
  const exportedAt = useProjectStore((s) => s.exportedAt);

  const selectedRunnerInfo = useSettingsStore((s) => {
    const runners = s.runners;
    return runners.find((r) => r.id === s.selectedRunner) ?? runners[0];
  });
  const publishStage = useSettingsStore((s) => s.publishStage);
  const setPublishStage = useSettingsStore((s) => s.setPublishStage);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);
  const addToast = useUiStore((s) => s.addToast);

  const processPages = useMemo(() => buildProcessPages(), []);

  const logLevelCounts = useMemo(() => {
    return bridgeLogs.reduce(
      (acc, row) => {
        if (row.level === "error") acc.error += 1;
        else if (row.level === "warn") acc.warn += 1;
        else acc.info += 1;
        return acc;
      },
      { info: 0, warn: 0, error: 0 },
    );
  }, [bridgeLogs]);

  const progressPercent = useMemo(() => {
    return processPages.length ? Math.round((6 / processPages.length) * 100) : 0;
  }, [processPages.length]);

  const [showAdvanced, setShowAdvanced] = useState(false);

  async function postJson(path: string, body: Record<string, unknown> = {}) {
    if (dryRunMode && path.startsWith("/api/run/")) {
      if (path.endsWith("/start")) {
        setRunState("running");
        pushLocalLog("info", `[dry-run] Simulated start (${String(body.scenario ?? scenario)}).`);
      } else if (path.endsWith("/retry")) {
        setRunState("retrying");
        pushLocalLog("warn", "[dry-run] Simulated retry with fixed port cleanup.");
      } else if (path.endsWith("/abort")) {
        setRunState("aborted");
        pushLocalLog("warn", "[dry-run] Simulated run abort.");
      }
      return { ok: true, dryRun: true };
    }
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Request failed");
    }
    return res.json();
  }

  async function startRun() {
    try {
      await postJson("/api/run/start", { runner: "bm", brandFolder, configPath, scenario, waves });
      setStatusMessage("Launch started.");
    } catch (error) {
      pushLocalLog("error", `Start failed: ${(error as Error).message}`);
    }
  }

  async function retryRun() {
    try {
      await postJson("/api/run/retry", { runner: "bm", brandFolder, configPath, scenario, waves });
      setStatusMessage("Retry started with fixed port policy.");
    } catch (error) {
      pushLocalLog("error", `Retry failed: ${(error as Error).message}`);
    }
  }

  async function abortRun() {
    try {
      await postJson("/api/run/abort", {});
      setStatusMessage("Run aborted.");
    } catch (error) {
      pushLocalLog("error", `Abort failed: ${(error as Error).message}`);
    }
  }

  async function startPublishStage(stageOverride?: string) {
    const stage = stageOverride || publishStage;
    try {
      await postJson("/api/publish/start", { stage, configPath });
      setStatusMessage(`Publish stage '${stage}' started.`);
    } catch (error) {
      pushLocalLog("error", `Publish failed: ${(error as Error).message}`);
    }
  }

  return (
    <section className="content-block priority-block">
      <h3>Launch Controls</h3>
      <div className="metric-grid">
        <article className="metric-card">
          <span>Journey completion</span>
          <strong>{progressPercent}%</strong>
        </article>
        <article className="metric-card">
          <span>Pages done</span>
          <strong>6 / {processPages.length}</strong>
        </article>
        <article className="metric-card">
          <span>Warnings + errors</span>
          <strong>{logLevelCounts.warn + logLevelCounts.error}</strong>
        </article>
        <article className="metric-card">
          <span>Runner</span>
          <strong>{selectedRunnerInfo?.label ?? "n/a"}</strong>
        </article>
      </div>
      <div className="progress-strip" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progressPercent}>
        <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
      </div>
      <div className="controls-row">
        <label className="field compact">
          Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
            <option value="surface">surface</option>
            <option value="focused">focused</option>
            <option value="comprehensive">comprehensive</option>
          </select>
        </label>
        <label className="field compact">
          Config path
          <div style={{ display: "flex", gap: 6 }}>
            <input style={{ flex: 1 }} value={configPath} onChange={(e) => setConfigPath(e.target.value)} />
            <button className="btn" onClick={async () => { const f = await pickYamlFile(); if (f) { setConfigPath(f); addToast(`Config: ${f}`, "success"); } }}>Browse…</button>
          </div>
        </label>
        <label className="field compact">
          Brand folder
          <div style={{ display: "flex", gap: 6 }}>
            <input style={{ flex: 1 }} value={brandFolder} onChange={(e) => setBrandFolder(e.target.value)} placeholder="./my-brand" />
            <button className="btn" onClick={async () => { const f = await pickFolder(); if (f) { setBrandFolder(f); addToast(`Brand folder: ${f}`, "success"); } }}>Browse…</button>
          </div>
        </label>
        <label className="field compact">
          Waves
          <input value={waves} onChange={(e) => setWaves(e.target.value)} placeholder="1-7" />
        </label>
      </div>
      <div className="controls-row">
        <button className="btn btn-primary" onClick={startRun} disabled={runState === "running"}>Start Launch</button>
        <button className="btn" onClick={retryRun} disabled={runState === "running"}>Retry on 4188</button>
        <button className="btn" onClick={abortRun} disabled={runState !== "running"}>Stop Run</button>
        <button className="btn" onClick={() => setSelectedPageId("process-settings")}>Provider Settings</button>
        <button className="btn" onClick={() => setShowAdvanced((prev) => !prev)}>
          {showAdvanced ? "Hide Advanced" : "More Options"}
        </button>
      </div>
      {showAdvanced && (
        <div className="content-block nested-block">
          <h4>Publishing controls</h4>
          <p>Wave 7 covers NotebookLM/Decks/Reports/Diagrams/Video. Wiki docs + Astro builder are post-pipeline steps.</p>
          <div className="controls-row">
            <label className="field compact">
              Publish stage
              <select value={publishStage} onChange={(e) => setPublishStage(e.target.value)}>
                <option value="notebooklm">notebooklm</option>
                <option value="decks">decks</option>
                <option value="reports">reports</option>
                <option value="diagrams">diagrams</option>
                <option value="video">video</option>
              </select>
            </label>
            <button className="btn" onClick={() => void startPublishStage()} disabled={runState === "running"}>Run bm publish</button>
          </div>
        </div>
      )}
      <div className="chip-row">
        <span>bridge: {bridgeOnline ? "online" : "offline"}</span>
        <span>state: {runState}</span>
        <span>mode: {dryRunMode ? "dry-run" : "live"}</span>
        <span>waves: {waves}</span>
      </div>
    </section>
  );
}


