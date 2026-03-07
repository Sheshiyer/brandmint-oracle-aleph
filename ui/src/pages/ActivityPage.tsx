import { useMemo, useState } from "react";
import { usePipelineStore } from "../stores/pipelineStore";
import { useUiStore } from "../stores/uiStore";
import { formatTime } from "../lib/utils";

export default function ActivityPage() {
  const bridgeLogs = usePipelineStore((s) => s.bridgeLogs);
  const addToast = useUiStore((s) => s.addToast);

  const [logLevelFilter, setLogLevelFilter] = useState<"all" | "info" | "warn" | "error">("all");
  const [compactLogs, setCompactLogs] = useState(false);
  const [logSearchQuery, setLogSearchQuery] = useState("");

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

  const searchFilteredLogs = useMemo(() => {
    const needle = logSearchQuery.trim().toLowerCase();
    const base = logLevelFilter === "all" ? bridgeLogs : bridgeLogs.filter((row) => row.level === logLevelFilter);
    if (!needle) return base;
    return base.filter((row) => row.message.toLowerCase().includes(needle));
  }, [bridgeLogs, logLevelFilter, logSearchQuery]);

  function exportLogs() {
    const text = searchFilteredLogs.map((row) => `[${row.ts}] [${row.level}] ${row.message}`).join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brandmint-logs-${new Date().toISOString().slice(0, 10)}.log`;
    a.click();
    URL.revokeObjectURL(url);
    addToast("Logs exported", "success");
  }

  return (
    <section className="content-block">
      <h3>Live Activity</h3>
      <div className="chip-row">
        <span>info {logLevelCounts.info}</span>
        <span>warn {logLevelCounts.warn}</span>
        <span>error {logLevelCounts.error}</span>
      </div>
      <div className="log-toolbar">
        <input value={logSearchQuery} onChange={(e) => setLogSearchQuery(e.target.value)} placeholder="Search logs..." />
        <label className="field compact">
          Level
          <select value={logLevelFilter} onChange={(e) => setLogLevelFilter(e.target.value as "all" | "info" | "warn" | "error")}>
            <option value="all">all</option>
            <option value="info">info</option>
            <option value="warn">warn</option>
            <option value="error">error</option>
          </select>
        </label>
        <button className={`btn ${compactLogs ? "btn-primary" : ""}`} onClick={() => setCompactLogs((prev) => !prev)}>
          {compactLogs ? "Compact" : "Full"}
        </button>
        <button className="btn" onClick={exportLogs}>Export .log</button>
        <span className="log-count">{searchFilteredLogs.length} entries</span>
      </div>
      <div className={`log-feed ${compactLogs ? "compact" : ""}`}>
        {searchFilteredLogs.slice(-240).map((log) => (
          <div key={log.id} className={`log-row ${log.level}`}>
            <span>{formatTime(log.ts)}</span>
            <strong>{log.level}</strong>
            <p>{log.message}</p>
          </div>
        ))}
        {!searchFilteredLogs.length && (
          <article className="empty-state">
            <h4>No logs match</h4>
            <p>Try a different filter or search term.</p>
          </article>
        )}
      </div>
    </section>
  );
}
