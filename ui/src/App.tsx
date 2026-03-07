import { useMemo } from "react";
import Shell from "./components/layout/Shell";
import { useUiStore } from "./stores/uiStore";
import { buildProcessPages } from "./lib/utils";
import type { PageKind } from "./types";

// ── Page imports ──
import LaunchPage from "./pages/LaunchPage";
import ActivityPage from "./pages/ActivityPage";
import IntakePage from "./pages/IntakePage";
import WizardPage from "./pages/WizardPage";
import ArtifactsPage from "./pages/ArtifactsPage";
import ReferencesPage from "./pages/ReferencesPage";
import SettingsPage from "./pages/SettingsPage";
import PublishPage from "./pages/PublishPage";

/** Maps a PageKind to the component that renders it */
function PageRouter({ kind }: { kind: PageKind }) {
  switch (kind) {
    case "launch":
      return <LaunchPage />;
    case "activity":
      return <ActivityPage />;
    case "intake":
      return <IntakePage />;
    case "extraction":
    case "wizard":
      return <WizardPage />;
    case "artifacts":
      return <ArtifactsPage />;
    case "reference-curation":
    case "reference-library":
      return <ReferencesPage />;
    case "settings":
      return <SettingsPage />;
    case "publish-notebooklm":
    case "wiki-handoff":
    case "astro-build":
      return <PublishPage />;
    case "export":
      return <StubPage title="Config Export" />;
    case "triage":
      return <StubPage title="Failure Triage" />;
    case "fal-dry-run":
      return <StubPage title="FAL Selection Dry Run" />;
    case "runner-workbench":
      return <StubPage title="Runner Workbench" />;
    case "runner-matrix":
      return <StubPage title="Runner Matrix" />;
    case "handoff":
      return <StubPage title="Delivery Handoff" />;
    case "history":
      return <StubPage title="Run History" />;
    case "output-viewer":
      return <StubPage title="Output Viewer" />;
    case "journey":
    default:
      return <JourneyStub />;
  }
}

function StubPage({ title }: { title: string }) {
  return (
    <section className="content-block">
      <h3>{title}</h3>
      <p style={{ color: "var(--fg-secondary)" }}>
        This page has been extracted as a component stub. Full implementation coming in next iteration.
      </p>
    </section>
  );
}

function JourneyStub() {
  const selectedPageId = useUiStore((s) => s.selectedPageId);
  const processPages = useMemo(() => buildProcessPages(), []);
  const page = processPages.find((p) => p.id === selectedPageId) ?? processPages[0];
  const idx = processPages.findIndex((p) => p.id === page?.id);

  if (!page) return null;

  return (
    <section className="journey-surface">
      <article className="journey-left">
        <span className="hero-label">Experience Surface</span>
        <h3 className="journey-title">{page.title}</h3>
        <p className="journey-description">{page.objective}</p>
        <div className="feature-stack">
          {page.focus.map((item, index) => (
            <div key={`${page.id}-${item}`} className="feature-row">
              <div className="f-number">{String(index + 1).padStart(2, "0")}</div>
              <div className="f-content">
                <h4 className="f-title">{item}</h4>
                <p className="f-desc">High clarity, low clutter implementation for this stage.</p>
              </div>
            </div>
          ))}
        </div>
      </article>
      <aside className="journey-right">
        <div className="scan-lines" />
        <div className="glitch-line" />
        <div className="overlay-ui">
          <span className="ui-badge">LIVE SURFACE</span>
          <span className="ui-coords">PAGE::{idx + 1} / {processPages.length}</span>
        </div>
        <div className="mesh-gallery">
          {page.focus.slice(0, 3).map((item, i) => (
            <div key={`${page.id}-mesh-${item}`} className="mesh-card">
              <div className={`wireframe-mesh mesh-shape-${i + 1}`}>
                <div className="mesh-inner" />
              </div>
              <div className="mesh-meta">
                <span>{item}</span>
                <span>ACTIVE</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </section>
  );
}

export default function App() {
  const selectedPageId = useUiStore((s) => s.selectedPageId);
  const processPages = useMemo(() => buildProcessPages(), []);
  const selectedPage = processPages.find((p) => p.id === selectedPageId) ?? processPages[0];

  return (
    <Shell>
      {selectedPage ? <PageRouter kind={selectedPage.kind} /> : <p>No page selected.</p>}
    </Shell>
  );
}
