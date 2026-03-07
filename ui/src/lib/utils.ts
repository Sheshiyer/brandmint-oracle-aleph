// ── Brandmint utility functions ─────────────────────────────────────

import type { ConfigDraft, ExtractedDraft, ProcessPage, Task, WaveGroup } from "../types";

export function summarizeLanes(tasks: Task[]) {
  return tasks.reduce<Record<string, number>>((acc, task) => {
    acc[task.dispatch_lane] = (acc[task.dispatch_lane] ?? 0) + 1;
    return acc;
  }, {});
}

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/[\s-]+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 2);
}

export function findPattern(text: string, patterns: RegExp[]): string {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) return match[1].trim();
  }
  return "";
}

export function cleanList(value: string): string {
  return value
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 6)
    .join("\n");
}

export function parseProductMd(markdown: string): ExtractedDraft {
  const text = markdown.replace(/\r\n/g, "\n");
  const lines = text.split("\n").map((line) => line.trim());
  const heading = lines.find((line) => /^#\s+/.test(line))?.replace(/^#+\s*/, "") ?? "";
  const firstParagraph =
    lines.find((line) => line.length > 40 && !line.startsWith("#") && !line.startsWith("-")) ?? "";
  const bullets = lines
    .filter((line) => /^[-*]\s+/.test(line))
    .map((line) => line.replace(/^[-*]\s+/, "").trim());

  const productName =
    heading || findPattern(text, [/product\s*name\s*[:\-]\s*(.+)/i, /name\s*[:\-]\s*(.+)/i]);
  const category = findPattern(text, [
    /category\s*[:\-]\s*(.+)/i,
    /domain\s*[:\-]\s*(.+)/i,
    /industry\s*[:\-]\s*(.+)/i,
  ]);
  const audience = findPattern(text, [
    /target\s+audience\s*[:\-]\s*(.+)/i,
    /audience\s*[:\-]\s*(.+)/i,
    /for\s+who\s*[:\-]\s*(.+)/i,
  ]);
  const problem = findPattern(text, [
    /problem\s*[:\-]\s*(.+)/i,
    /pain\s*points?\s*[:\-]\s*(.+)/i,
    /challenge\s*[:\-]\s*(.+)/i,
  ]);
  const valueProposition =
    findPattern(text, [
      /value\s+proposition\s*[:\-]\s*(.+)/i,
      /promise\s*[:\-]\s*(.+)/i,
      /solution\s*[:\-]\s*(.+)/i,
    ]) || firstParagraph;
  const differentiatorBullets = bullets
    .filter((line) => /feature|differentiator|advantage|benefit|proof|unique/i.test(line))
    .slice(0, 5);
  const differentiators = cleanList(
    (differentiatorBullets.length ? differentiatorBullets : bullets).join("\n"),
  );
  const voiceTone = findPattern(text, [
    /voice\s*(?:and|&)\s*tone\s*[:\-]\s*(.+)/i,
    /tone\s*[:\-]\s*(.+)/i,
    /voice\s*[:\-]\s*(.+)/i,
  ]);
  const launchGoal = findPattern(text, [
    /launch\s+goal\s*[:\-]\s*(.+)/i,
    /objective\s*[:\-]\s*(.+)/i,
    /cta\s*[:\-]\s*(.+)/i,
  ]);

  const fields = [
    productName,
    category,
    audience,
    problem,
    valueProposition,
    differentiators,
    voiceTone,
    launchGoal,
  ];
  const confidence = Number((fields.filter(Boolean).length / fields.length).toFixed(2));

  return {
    productName,
    category,
    audience,
    problem,
    valueProposition,
    differentiators,
    voiceTone,
    launchGoal,
    confidence,
  };
}

export function extractionToConfig(extraction: ExtractedDraft): ConfigDraft {
  return {
    brand: {
      name: extraction.productName || "Brandmint Product",
      domain: extraction.category || "ai-product",
      voice: extraction.voiceTone || "confident, clear",
      tone: extraction.voiceTone || "premium, calm",
    },
    audience: {
      personaName: extraction.audience || "Growth team",
      painPoints: extraction.problem || "Need stronger brand coherence",
    },
    positioning: {
      statement:
        extraction.valueProposition ||
        "Transforms product notes into launch-ready brand assets.",
      pillars: extraction.differentiators || "clarity\nconsistency\nvelocity",
    },
    campaign: {
      primaryObjective: extraction.launchGoal || "Drive first conversion cycle",
    },
    visual: {
      paletteMood: "quiet luxury + editorial grid",
      typography: "clean, high-contrast sans",
      surfaceStyle: "glass + soft depth",
    },
  };
}

export function configToYaml(config: ConfigDraft): string {
  const lines = [
    "brand:",
    `  name: "${config.brand.name}"`,
    `  domain: "${config.brand.domain}"`,
    `  voice: "${config.brand.voice}"`,
    `  tone: "${config.brand.tone}"`,
    "audience:",
    `  persona_name: "${config.audience.personaName}"`,
    `  pain_points: "${config.audience.painPoints.replace(/\n/g, " | ")}"`,
    "positioning:",
    `  statement: "${config.positioning.statement}"`,
    "  pillars:",
    ...config.positioning.pillars
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => `    - "${line}"`),
    "campaign:",
    `  primary_objective: "${config.campaign.primaryObjective}"`,
    "visual:",
    `  palette_mood: "${config.visual.paletteMood}"`,
    `  typography: "${config.visual.typography}"`,
    `  surface_style: "${config.visual.surfaceStyle}"`,
  ];
  return lines.join("\n");
}

export function downloadText(fileName: string, content: string, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function bytesToHuman(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatTime(input: string): string {
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) return input;
  return date.toLocaleString();
}

export function suggestRecovery(message: string): { label: string; steps: string[] } {
  const normalized = message.toLowerCase();
  if (normalized.includes("port") || normalized.includes("listen")) {
    return {
      label: "Port contention",
      steps: [
        "Use Retry on 4188 to auto-clear stale listeners.",
        "Check if another local process is pinned to 4188.",
      ],
    };
  }
  if (normalized.includes("config")) {
    return {
      label: "Configuration mismatch",
      steps: [
        "Re-open Config Wizard page and verify required fields.",
        "Re-export config and relaunch with updated path.",
      ],
    };
  }
  if (normalized.includes("timeout") || normalized.includes("network")) {
    return {
      label: "Runtime timeout",
      steps: [
        "Retry run after reducing wave scope to 1-4.",
        "Check backend bridge health and relaunch the run.",
      ],
    };
  }
  return {
    label: "General failure",
    steps: [
      "Review latest error line in Live Activity.",
      "Retry run and capture the next failing step for triage.",
    ],
  };
}

export function defaultConfigDraft(): ConfigDraft {
  return {
    brand: {
      name: "",
      domain: "",
      voice: "",
      tone: "",
    },
    audience: {
      personaName: "",
      painPoints: "",
    },
    positioning: {
      statement: "",
      pillars: "",
    },
    campaign: {
      primaryObjective: "",
    },
    visual: {
      paletteMood: "quiet luxury + editorial grid",
      typography: "clean, high-contrast sans",
      surfaceStyle: "glass + soft depth",
    },
  };
}

export function buildProcessPages(): ProcessPage[] {
  const pages: ProcessPage[] = [
    { id: "journey-01", title: "Welcome & Brand Setup", track: "Brand Experience Journey", kind: "journey", objective: "Give users a clean, premium first screen to start a brand run confidently.", focus: ["Project setup", "Scenario intent", "Guided start"] },
    { id: "journey-02", title: "Campaign Intent & Success Criteria", track: "Brand Experience Journey", kind: "journey", objective: "Capture what success means before users upload or generate anything.", focus: ["Primary goal", "KPI framing", "Constraints"] },
    { id: "process-intake", title: "Product MD Intake", track: "Brand Experience Journey", kind: "intake", objective: "Capture complete product context before synthesis.", focus: ["Upload", "Paste", "Draft restore"] },
    { id: "journey-03", title: "Input Quality Diagnostics", track: "Brand Experience Journey", kind: "journey", objective: "Show if Product MD quality is sufficient for high-confidence extraction.", focus: ["Completeness score", "Missing fields", "Fix tips"] },
    { id: "process-extraction", title: "Extraction Review", track: "Brand Experience Journey", kind: "extraction", objective: "Validate extracted signals before config generation.", focus: ["Confidence", "Field edits", "Confirm"] },
    { id: "journey-04", title: "Signal Confidence Tuning", track: "Brand Experience Journey", kind: "journey", objective: "Tune low-confidence sections before moving into the wizard.", focus: ["Trust score", "Suggested edits", "Approve"] },
    { id: "journey-05", title: "Brand Basics Setup", track: "Brand Experience Journey", kind: "journey", objective: "Guide naming, domain, and base identity structure.", focus: ["Brand name", "Domain", "Category fit"] },
    { id: "journey-06", title: "Audience Definition", track: "Brand Experience Journey", kind: "journey", objective: "Capture persona and pain points with minimal friction.", focus: ["Persona", "Pain points", "Priority needs"] },
    { id: "journey-07", title: "Positioning & Promise", track: "Brand Experience Journey", kind: "journey", objective: "Turn product signals into clear market positioning.", focus: ["Positioning", "Differentiators", "Proof cues"] },
    { id: "journey-08", title: "Voice & Tone Crafting", track: "Brand Experience Journey", kind: "journey", objective: "Lock communication style before asset generation.", focus: ["Voice", "Tone", "Copy examples"] },
    { id: "journey-09", title: "Visual Direction Curation", track: "Brand Experience Journey", kind: "journey", objective: "Translate brand intent into visual direction.", focus: ["Palette mood", "Typography", "Surface style"] },
    { id: "process-wizard", title: "Brand Config Wizard", track: "Brand Experience Journey", kind: "wizard", objective: "Shape brand, audience, positioning, and visual system.", focus: ["5 steps", "Guided", "Editable"] },
    { id: "journey-10", title: "Configuration QA Review", track: "Brand Experience Journey", kind: "journey", objective: "Validate data consistency and readiness before export.", focus: ["Completeness", "Consistency", "Readiness"] },
    { id: "process-export", title: "Config Export", track: "Brand Experience Journey", kind: "export", objective: "Export ready-to-run brand config artifacts.", focus: ["YAML", "JSON", "Handoff"] },
    { id: "journey-11", title: "Reference Prioritization Logic", track: "Brand Experience Journey", kind: "journey", objective: "Explain why references are ranked for this brand context.", focus: ["Tag relevance", "Brand fit", "Priority"] },
    { id: "process-ref-curation", title: "Reference Curation (Top 30)", track: "Brand Experience Journey", kind: "reference-curation", objective: "Show the 30 most relevant references by synthesis score.", focus: ["Top 30", "Primary assets", "Selection"] },
    { id: "process-ref-library", title: "Reference Library (Show More)", track: "Brand Experience Journey", kind: "reference-library", objective: "Let operators progressively load more references.", focus: ["Show more", "Browse all", "Filter mentally"] },
    { id: "journey-12", title: "Style Cluster Explorer", track: "Brand Experience Journey", kind: "journey", objective: "Explore grouped visual directions before final selection.", focus: ["Clusters", "Mood grouping", "Compare"] },
    { id: "journey-13", title: "Prompt Scaffold Builder", track: "Brand Experience Journey", kind: "journey", objective: "Assemble prompt scaffolds from approved brand signals.", focus: ["Prompt blocks", "Templates", "Consistency"] },
    { id: "journey-14", title: "Prompt QA Harness", track: "Brand Experience Journey", kind: "journey", objective: "Quality-check prompt scaffolding before generation.", focus: ["Coverage", "Quality checks", "Risk notes"] },
    { id: "process-fal", title: "FAL Selection Dry Run", track: "Brand Experience Journey", kind: "fal-dry-run", objective: "Simulate image generation queue from selected references.", focus: ["Dry run", "Preview outputs", "Queue confidence"] },
    { id: "journey-15", title: "Generation Queue Preview", track: "Brand Experience Journey", kind: "journey", objective: "Preview what will be generated and in what order.", focus: ["Queue order", "Asset intent", "Runtime estimate"] },
    { id: "journey-16", title: "Variant Compare Board", track: "Brand Experience Journey", kind: "journey", objective: "Enable side-by-side review of generated variants.", focus: ["A/B compare", "Notes", "Promote winners"] },
    { id: "process-launch", title: "Launch Controls", track: "Launch & Operations", kind: "launch", objective: "Operate bm launch with safe retry policy on 4188.", focus: ["Start", "Retry", "Abort"] },
    { id: "process-activity", title: "Live Activity Stream", track: "Launch & Operations", kind: "activity", objective: "Observe real-time execution and orchestration feedback.", focus: ["Logs", "State", "Bridge"] },
    { id: "process-triage", title: "Failure Triage", track: "Launch & Operations", kind: "triage", objective: "Convert failures into fast recovery actions.", focus: ["Error patterns", "Recovery", "Retry loop"] },
    { id: "process-settings", title: "Provider Settings", track: "Launch & Operations", kind: "settings", objective: "Configure OpenRouter/NBrain keys and model routing defaults.", focus: ["API keys", "Model router", "Provider readiness"] },
    { id: "process-runner", title: "Runner Workbench", track: "Launch & Operations", kind: "runner-workbench", objective: "Run docs/prompt generation through modular providers.", focus: ["Claude", "Codex", "Gemini/OpenRouter"] },
    { id: "process-runner-matrix", title: "Runner Availability Matrix", track: "Launch & Operations", kind: "runner-matrix", objective: "Understand provider capabilities and runtime readiness.", focus: ["PTY", "Prompt required", "Availability"] },
    { id: "process-artifacts", title: "Artifacts Browser", track: "Launch & Operations", kind: "artifacts", objective: "Inspect outputs and state files in one focused page.", focus: ["outputs", "deliverables", "state"] },
    { id: "process-handoff", title: "Delivery Handoff", track: "Launch & Operations", kind: "handoff", objective: "Prepare final handoff package and next actions.", focus: ["Config path", "Selected refs", "Deliverables"] },
    { id: "process-notebooklm", title: "Wave 7B · NotebookLM Publish", track: "Publishing & Docs Waves", kind: "publish-notebooklm", objective: "Run NotebookLM deliverable generation as part of publishing.", focus: ["bm publish notebooklm", "audio + notebook", "publish logs"] },
    { id: "process-wiki-handoff", title: "Wave 8A · Wiki Docs Handoff", track: "Publishing & Docs Waves", kind: "wiki-handoff", objective: "Prepare wiki docs generation handoff from .brandmint outputs.", focus: ["wiki-doc-generator", "parallel agents", "handoff checklist"] },
    { id: "process-astro-build", title: "Wave 8B · Astro Build Handoff", track: "Publishing & Docs Waves", kind: "astro-build", objective: "Prepare markdown-to-astro conversion and Astro build handoff.", focus: ["markdown-to-astro-wiki", "content mapping", "site build"] },
    { id: "process-history", title: "Run History", track: "Launch & Operations", kind: "history", objective: "Browse past pipeline runs with duration, status, and configuration.", focus: ["Past runs", "Duration", "Status"] },
    { id: "process-output-viewer", title: "Output Viewer", track: "Launch & Operations", kind: "output-viewer", objective: "Inspect skill output JSON files with syntax highlighting.", focus: ["JSON tree", "Collapsible", "Search"] },
    { id: "journey-21", title: "Logo Direction Studio", track: "Visual Creation Surfaces", kind: "journey", objective: "Explore and shortlist logo directions aligned to extracted brand intent.", focus: ["Wordmark options", "Icon variants", "Keep/discard"] },
    { id: "journey-22", title: "Typography Pairing Studio", track: "Visual Creation Surfaces", kind: "journey", objective: "Preview and compare font pairings for readability and brand voice.", focus: ["Primary font", "Secondary font", "Readability"] },
    { id: "journey-23", title: "Palette Application Board", track: "Visual Creation Surfaces", kind: "journey", objective: "Apply palette options to key UI and campaign mock blocks.", focus: ["Primary palette", "Accent behavior", "Contrast"] },
    { id: "journey-24", title: "Campaign Asset Matrix", track: "Visual Creation Surfaces", kind: "journey", objective: "Map selected outputs into channel-ready campaign slots.", focus: ["Social slots", "Landing hero", "Ad variants"] },
    { id: "journey-25", title: "Final Delivery Package", track: "Visual Creation Surfaces", kind: "journey", objective: "Bundle final selections and export package for publishing handoff.", focus: ["Final bundle", "Download set", "Publish-ready"] },
  ];
  return pages;
}

export function waveForPage(page: ProcessPage): { id: string; label: string } {
  const journeyMatch = page.id.match(/^journey-(\d+)/);
  const journeyNumber = journeyMatch ? Number(journeyMatch[1]) : null;

  if (
    page.kind === "intake" ||
    page.kind === "extraction" ||
    page.kind === "wizard" ||
    page.kind === "export" ||
    (journeyNumber !== null && journeyNumber >= 1 && journeyNumber <= 10)
  ) {
    return { id: "wave-1", label: "Wave 1 · Foundations" };
  }
  if (
    page.kind === "reference-curation" ||
    page.kind === "reference-library" ||
    (journeyNumber !== null && journeyNumber >= 11 && journeyNumber <= 14)
  ) {
    return { id: "wave-2", label: "Wave 2 · References + Prompting" };
  }
  if (page.kind === "fal-dry-run" || (journeyNumber !== null && journeyNumber >= 15 && journeyNumber <= 16)) {
    return { id: "wave-3", label: "Wave 3 · Generation Prep" };
  }
  if (page.kind === "settings" || page.kind === "history" || page.kind === "output-viewer") {
    return { id: "wave-app", label: "App" };
  }
  if (
    page.kind === "launch" ||
    page.kind === "activity" ||
    page.kind === "triage" ||
    page.kind === "runner-workbench" ||
    page.kind === "runner-matrix"
  ) {
    return { id: "wave-4", label: "Wave 4 · Run Orchestration" };
  }
  if (page.kind === "artifacts" || page.kind === "handoff") {
    return { id: "wave-5", label: "Wave 5 · Delivery + Handoff" };
  }
  if (page.kind === "publish-notebooklm") {
    return { id: "wave-7", label: "Wave 7 · Publishing Deliverables" };
  }
  if (page.kind === "wiki-handoff" || page.kind === "astro-build") {
    return { id: "wave-8", label: "Wave 8 · Docs + Astro Handoff" };
  }
  if (journeyNumber !== null && journeyNumber >= 21) {
    return { id: "wave-6", label: "Wave 6 · Visual Surfaces" };
  }
  return { id: "wave-x", label: "Additional Surfaces" };
}

/** Group pages by wave, maintaining canonical order */
export function groupPagesByWave(pages: ProcessPage[]): WaveGroup[] {
  const grouped = pages.reduce<Record<string, WaveGroup>>((acc, page) => {
    const wave = waveForPage(page);
    if (!acc[wave.id]) {
      acc[wave.id] = { id: wave.id, label: wave.label, pages: [] };
    }
    acc[wave.id].pages.push(page);
    return acc;
  }, {});
  const order = ["wave-1", "wave-2", "wave-3", "wave-4", "wave-5", "wave-6", "wave-7", "wave-8", "wave-app", "wave-x"];
  return order.map((id) => grouped[id]).filter(Boolean) as WaveGroup[];
}
