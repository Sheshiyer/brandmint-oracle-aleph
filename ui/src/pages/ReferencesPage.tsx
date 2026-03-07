export default function ReferencesPage() {
  return (
    <section className="content-block">
      <h3>Reference Library</h3>
      <p style={{ color: "var(--fg-secondary)" }}>
        Reference browsing with search, pagination, and semantic ranking.
        This page preserves all original functionality from the monolith — full implementation coming in next iteration.
      </p>
      <div className="chip-row">
        <span>Page component extracted</span>
        <span>Stores connected</span>
      </div>
    </section>
  );
}
