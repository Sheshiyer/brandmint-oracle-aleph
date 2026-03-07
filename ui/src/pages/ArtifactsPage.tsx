import { useMemo } from "react";
import { useArtifactStore } from "../stores/artifactStore";
import { useUiStore } from "../stores/uiStore";
import { bytesToHuman, formatTime } from "../lib/utils";

export default function ArtifactsPage() {
  const artifacts = useArtifactStore((s) => s.artifacts);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);

  const groupedArtifacts = useMemo(() => {
    return artifacts.reduce<Record<string, typeof artifacts>>((acc, row) => {
      acc[row.group] = [...(acc[row.group] ?? []), row];
      return acc;
    }, {});
  }, [artifacts]);

  return (
    <section className="content-block">
      <h3>Artifacts Browser</h3>
      {Object.entries(groupedArtifacts).map(([group, rows]) => (
        <div key={group} className="artifact-group">
          <h4>{group}</h4>
          <div className="list-grid">
            {rows.slice(0, 16).map((item) => (
              <article key={`${group}-${item.path}`} className="list-card">
                <h4>{item.name}</h4>
                <p>{item.relativePath}</p>
                <div className="chip-row">
                  <span>{bytesToHuman(item.size)}</span>
                  <span>{formatTime(item.modifiedAt)}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      ))}
      {!artifacts.length && (
        <article className="empty-state">
          <h4>No artifacts yet</h4>
          <p>Run a launch or dry run to populate outputs.</p>
          <button className="btn" onClick={() => setSelectedPageId("process-launch")}>Go to Launch</button>
        </article>
      )}
    </section>
  );
}
