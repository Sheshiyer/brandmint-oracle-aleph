import { useProjectStore } from "../stores/projectStore";
import { usePipelineStore } from "../stores/pipelineStore";
import { useUiStore } from "../stores/uiStore";
import { extractionToConfig } from "../lib/utils";

export default function WizardPage() {
  const extraction = useProjectStore((s) => s.extraction);
  const extractionConfirmed = useProjectStore((s) => s.extractionConfirmed);
  const setExtractionConfirmed = useProjectStore((s) => s.setExtractionConfirmed);
  const wizardStep = useProjectStore((s) => s.wizardStep);
  const setWizardStep = useProjectStore((s) => s.setWizardStep);
  const configDraft = useProjectStore((s) => s.configDraft);
  const setConfigDraft = useProjectStore((s) => s.setConfigDraft);
  const updateConfigDraft = useProjectStore((s) => s.updateConfigDraft);
  const setExtraction = useProjectStore((s) => s.setExtraction);

  const setStatusMessage = usePipelineStore((s) => s.setStatusMessage);
  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);

  // If on extraction review
  if (!extractionConfirmed) {
    return (
      <section className="content-block">
        <h3>Extraction Review</h3>
        <div className="chip-row">
          <span>confidence {(extraction.confidence * 100).toFixed(0)}%</span>
          <span>{extractionConfirmed ? "confirmed" : "not confirmed"}</span>
        </div>
        <div className="page-form-grid">
          <label className="field">
            Product name
            <input value={extraction.productName} onChange={(e) => setExtraction({ ...extraction, productName: e.target.value })} />
          </label>
          <label className="field">
            Category
            <input value={extraction.category} onChange={(e) => setExtraction({ ...extraction, category: e.target.value })} />
          </label>
          <label className="field">
            Audience
            <input value={extraction.audience} onChange={(e) => setExtraction({ ...extraction, audience: e.target.value })} />
          </label>
          <label className="field">
            Problem
            <textarea className="field-textarea short" value={extraction.problem} onChange={(e) => setExtraction({ ...extraction, problem: e.target.value })} />
          </label>
          <label className="field">
            Value proposition
            <textarea className="field-textarea short" value={extraction.valueProposition} onChange={(e) => setExtraction({ ...extraction, valueProposition: e.target.value })} />
          </label>
          <label className="field">
            Differentiators
            <textarea className="field-textarea short" value={extraction.differentiators} onChange={(e) => setExtraction({ ...extraction, differentiators: e.target.value })} />
          </label>
          <label className="field">
            Voice and tone
            <input value={extraction.voiceTone} onChange={(e) => setExtraction({ ...extraction, voiceTone: e.target.value })} />
          </label>
          <label className="field">
            Launch goal
            <input value={extraction.launchGoal} onChange={(e) => setExtraction({ ...extraction, launchGoal: e.target.value })} />
          </label>
        </div>
        <div className="controls-row">
          <button className="btn btn-primary" onClick={() => {
            setConfigDraft(extractionToConfig(extraction));
            setExtractionConfirmed(true);
            setWizardStep(0);
            setStatusMessage("Extraction confirmed. Wizard draft generated.");
            setSelectedPageId("process-wizard");
          }}>
            Confirm and Continue
          </button>
        </div>
      </section>
    );
  }

  const STEPS = ["Brand Basics", "Audience", "Voice", "Visual", "Review"];

  function renderWizardPane() {
    switch (wizardStep) {
      case 0:
        return (
          <div className="page-form-grid">
            <label className="field">
              Brand name
              <input value={configDraft.brand.name} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, name: e.target.value } }))} />
            </label>
            <label className="field">
              Domain / category
              <input value={configDraft.brand.domain} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, domain: e.target.value } }))} />
            </label>
          </div>
        );
      case 1:
        return (
          <div className="page-form-grid">
            <label className="field">
              Persona
              <input value={configDraft.audience.personaName} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, audience: { ...prev.audience, personaName: e.target.value } }))} />
            </label>
            <label className="field">
              Pain points
              <textarea className="field-textarea short" value={configDraft.audience.painPoints} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, audience: { ...prev.audience, painPoints: e.target.value } }))} />
            </label>
          </div>
        );
      case 2:
        return (
          <div className="page-form-grid">
            <label className="field">
              Voice
              <input value={configDraft.brand.voice} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, voice: e.target.value } }))} />
            </label>
            <label className="field">
              Tone
              <input value={configDraft.brand.tone} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, tone: e.target.value } }))} />
            </label>
          </div>
        );
      case 3:
        return (
          <div className="page-form-grid">
            <label className="field">
              Palette mood
              <input value={configDraft.visual.paletteMood} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, paletteMood: e.target.value } }))} />
            </label>
            <label className="field">
              Typography
              <input value={configDraft.visual.typography} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, typography: e.target.value } }))} />
            </label>
            <label className="field">
              Surface style
              <input value={configDraft.visual.surfaceStyle} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, surfaceStyle: e.target.value } }))} />
            </label>
          </div>
        );
      case 4:
      default:
        return (
          <div className="page-form-grid">
            <label className="field">
              Positioning statement
              <textarea className="field-textarea short" value={configDraft.positioning.statement} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, positioning: { ...prev.positioning, statement: e.target.value } }))} />
            </label>
            <label className="field">
              Positioning pillars (line separated)
              <textarea className="field-textarea short" value={configDraft.positioning.pillars} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, positioning: { ...prev.positioning, pillars: e.target.value } }))} />
            </label>
            <label className="field">
              Campaign objective
              <input value={configDraft.campaign.primaryObjective} onChange={(e) => updateConfigDraft((prev) => ({ ...prev, campaign: { ...prev.campaign, primaryObjective: e.target.value } }))} />
            </label>
          </div>
        );
    }
  }

  return (
    <section className="content-block">
      <h3>Brand Config Wizard</h3>
      <div className="wizard-rail-modern">
        {STEPS.map((label, idx) => (
          <button
            key={label}
            className={`wizard-pill ${idx === wizardStep ? "active" : ""}`}
            onClick={() => setWizardStep(idx)}
            disabled={!extractionConfirmed}
          >
            {idx + 1}. {label}
          </button>
        ))}
      </div>
      {renderWizardPane()}
      <div className="controls-row">
        <button className="btn" onClick={() => setWizardStep(Math.max(0, wizardStep - 1))}>Prev</button>
        <button className="btn" onClick={() => setWizardStep(Math.min(4, wizardStep + 1))}>Next</button>
        <button className="btn btn-primary" onClick={() => setSelectedPageId("process-export")}>Go to Export</button>
      </div>
    </section>
  );
}
