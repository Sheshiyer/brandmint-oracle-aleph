import { usePipelineStore } from "../stores/pipelineStore";
import { useProjectStore } from "../stores/projectStore";
import { useSettingsStore } from "../stores/settingsStore";
import { useUiStore } from "../stores/uiStore";

export default function PublishPage() {
  const runState = usePipelineStore((s) => s.runState);
  const pushLocalLog = usePipelineStore((s) => s.pushLocalLog);
  const setStatusMessage = usePipelineStore((s) => s.setStatusMessage);
  const activeRunnerId = usePipelineStore((s) => s.activeRunnerId);
  const dryRunMode = usePipelineStore((s) => s.dryRunMode);
  const setRunState = usePipelineStore((s) => s.setRunState);

  const configPath = useProjectStore((s) => s.configPath);
  const wikiHandoffDone = useProjectStore((s) => s.wikiHandoffDone);
  const setWikiHandoffDone = useProjectStore((s) => s.setWikiHandoffDone);
  const astroHandoffDone = useProjectStore((s) => s.astroHandoffDone);
  const setAstroHandoffDone = useProjectStore((s) => s.setAstroHandoffDone);

  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);

  async function startPublishStage(stage: string) {
    try {
      if (dryRunMode) {
        setRunState("running");
        pushLocalLog("info", `[dry-run] Simulated publish stage: ${stage}`);
        return;
      }
      const res = await fetch("/api/publish/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage, configPath }),
      });
      if (!res.ok) throw new Error("Publish request failed");
      setStatusMessage(`Publish stage '${stage}' started.`);
    } catch (error) {
      pushLocalLog("error", `Publish failed: ${(error as Error).message}`);
    }
  }

  return (
    <div>
      {/* NotebookLM section */}
      <section className="content-block">
        <h3>Wave 7B · NotebookLM Publish</h3>
        <p>This runs the publishing deliverable for NotebookLM (and audio bundle) using your selected config.</p>
        <div className="chip-row">
          <span>command bm publish notebooklm --config {configPath}</span>
          <span>runner {activeRunnerId}</span>
        </div>
        <div className="controls-row">
          <button className="btn btn-primary" onClick={() => void startPublishStage("notebooklm")}>
            Run NotebookLM Publish
          </button>
          <button className="btn" onClick={() => setSelectedPageId("process-activity")}>View Logs</button>
        </div>
      </section>

      {/* Wiki handoff */}
      <section className="content-block" style={{ marginTop: 16 }}>
        <h3>Wave 8A · Wiki Docs Handoff</h3>
        <p>Post-pipeline step: run the <strong>wiki-doc-generator</strong> skill against <code>.brandmint/outputs/*.json</code>.</p>
        <div className="controls-row">
          <button
            className={`btn ${wikiHandoffDone ? "btn-primary" : ""}`}
            onClick={() => {
              setWikiHandoffDone(!wikiHandoffDone);
              pushLocalLog("info", `Wiki handoff marked ${!wikiHandoffDone ? "done" : "pending"}.`);
            }}
          >
            {wikiHandoffDone ? "Wiki Handoff Done" : "Mark Wiki Handoff Done"}
          </button>
        </div>
      </section>

      {/* Astro handoff */}
      <section className="content-block" style={{ marginTop: 16 }}>
        <h3>Wave 8B · Astro Build Handoff</h3>
        <p>Post-wiki step: use <strong>markdown-to-astro-wiki</strong> flow to build the glassmorphism Astro docs site.</p>
        <div className="controls-row">
          <button
            className={`btn ${astroHandoffDone ? "btn-primary" : ""}`}
            onClick={() => {
              setAstroHandoffDone(!astroHandoffDone);
              pushLocalLog("info", `Astro handoff marked ${!astroHandoffDone ? "done" : "pending"}.`);
            }}
          >
            {astroHandoffDone ? "Astro Handoff Done" : "Mark Astro Handoff Done"}
          </button>
        </div>
      </section>
    </div>
  );
}
