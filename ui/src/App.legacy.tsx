import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import type { JSX } from "react";

type RunState = "idle" | "running" | "retrying" | "aborted";

type Task = {
  id: string;
  title: string;
  area: string;
  owner_role: string;
  est_hours: number;
  dependencies: string[];
  deliverable: string;
  acceptance: string;
  dispatch_lane: string;
  parallelizable: boolean;
  wave: string;
  sprint: string;
};

type Sprint = {
  sprint_id: string;
  duration_weeks: number;
  focus: string;
  tasks: Task[];
};

type Phase = {
  phase_id: string;
  name: string;
  objective: string;
  sprints: Sprint[];
};

type TaskmasterPlan = {
  schema_version: string;
  project: {
    name: string;
    totals: {
      tasks: number;
      phases: number;
      sprints: number;
    };
  };
  phases: Phase[];
};

type BridgeLog = {
  id: number;
  ts: string;
  level: string;
  message: string;
};

type ArtifactItem = {
  name: string;
  path: string;
  relativePath: string;
  size: number;
  modifiedAt: string;
  extension: string;
  group: string;
};

type ReferenceImage = {
  id: string;
  name: string;
  relativePath: string;
  url: string;
  description: string;
  tags: string[];
  sources: string[];
  priority: number;
  assetIds: string[];
  size: number;
};

type RunnerInfo = {
  id: string;
  label: string;
  kind: string;
  available: boolean;
  supportsOutputPath: boolean;
  requiresPrompt: boolean;
  pty: boolean;
  description: string;
};

type IntegrationSettings = {
  openrouter: {
    model: string;
    routeMode: string;
    endpoint: string;
    hasApiKey: boolean;
    apiKeyMasked: string;
  };
  nbrain: {
    enabled: boolean;
    model: string;
    endpoint: string;
    hasApiKey: boolean;
    apiKeyMasked: string;
  };
  defaults: {
    preferredRunner: string;
  };
};

type PhaseSummary = Phase & {
  index: number;
  taskCount: number;
  estimatedHours: number;
  laneCounts: Record<string, number>;
  tasks: Task[];
};

type ExtractedDraft = {
  productName: string;
  category: string;
  audience: string;
  problem: string;
  valueProposition: string;
  differentiators: string;
  voiceTone: string;
  launchGoal: string;
  confidence: number;
};

type ConfigDraft = {
  brand: {
    name: string;
    domain: string;
    voice: string;
    tone: string;
  };
  audience: {
    personaName: string;
    painPoints: string;
  };
  positioning: {
    statement: string;
    pillars: string;
  };
  campaign: {
    primaryObjective: string;
  };
  visual: {
    paletteMood: string;
    typography: string;
    surfaceStyle: string;
  };
};

type PageKind =
  | "journey"
  | "intake"
  | "extraction"
  | "wizard"
  | "export"
  | "launch"
  | "activity"
  | "triage"
  | "settings"
  | "reference-curation"
  | "reference-library"
  | "fal-dry-run"
  | "runner-workbench"
  | "runner-matrix"
  | "artifacts"
  | "handoff"
  | "publish-notebooklm"
  | "wiki-handoff"
  | "astro-build"
  | "history"
  | "output-viewer";

type ProcessPage = {
  id: string;
  title: string;
  track: string;
  kind: PageKind;
  objective: string;
  focus: string[];
};

type PageStatus = "pending" | "active" | "done" | "attention";
type WaveGroup = {
  id: string;
  label: string;
  pages: ProcessPage[];
};
type CommandAction = {
  id: string;
  label: string;
  hint?: string;
  run: () => void;
};

type Toast = {
  id: number;
  message: string;
  kind: "success" | "error" | "info";
  exiting?: boolean;
};

type RunHistoryEntry = {
  id: string;
  scenario: string;
  waves: string;
  startedAt: string;
  duration: number;
  status: "success" | "failed" | "aborted";
  projectName: string;
  configPath: string;
};

type RecentProject = {
  name: string;
  path: string;
  lastOpened: string;
  scenario: string;
};

type AppPreferences = {
  fontSize: "default" | "large" | "xlarge";
  sidebarWidth: number;
  autoSave: boolean;
  showNotifications: boolean;
  logRetention: number;
};

const DEFAULT_PREFERENCES: AppPreferences = {
  fontSize: "large",
  sidebarWidth: 280,
  autoSave: true,
  showNotifications: true,
  logRetention: 500,
};

const HISTORY_KEY = "brandmint-run-history";
const PROJECTS_KEY = "brandmint-recent-projects";
const PREFS_KEY = "brandmint-preferences";
const DRAFT_KEY = "brandmint-process-studio-v3";
const DEFAULT_TASK_PROMPT =
  "Generate a markdown update for this brand run with completed work, risks, and next steps.";

const DEFAULT_INTEGRATION_SETTINGS: IntegrationSettings = {
  openrouter: {
    model: "openai/gpt-4o-mini",
    routeMode: "balanced",
    endpoint: "https://openrouter.ai/api/v1/chat/completions",
    hasApiKey: false,
    apiKeyMasked: "",
  },
  nbrain: {
    enabled: false,
    model: "nbrain/default",
    endpoint: "",
    hasApiKey: false,
    apiKeyMasked: "",
  },
  defaults: {
    preferredRunner: "bm",
  },
};

const FALLBACK_RUNNERS: RunnerInfo[] = [
  {
    id: "bm",
    label: "Brandmint Pipeline",
    kind: "pipeline",
    available: true,
    supportsOutputPath: false,
    requiresPrompt: false,
    pty: false,
    description: "Runs bm launch pipeline with waves/scenario.",
  },
];

const emptyExtraction: ExtractedDraft = {
  productName: "",
  category: "",
  audience: "",
  problem: "",
  valueProposition: "",
  differentiators: "",
  voiceTone: "",
  launchGoal: "",
  confidence: 0,
};

function defaultConfigDraft(): ConfigDraft {
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

function summarizeLanes(tasks: Task[]) {
  return tasks.reduce<Record<string, number>>((acc, task) => {
    acc[task.dispatch_lane] = (acc[task.dispatch_lane] ?? 0) + 1;
    return acc;
  }, {});
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/[\s-]+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 2);
}

function findPattern(text: string, patterns: RegExp[]): string {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match?.[1]) return match[1].trim();
  }
  return "";
}

function cleanList(value: string): string {
  return value
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 6)
    .join("\n");
}

function parseProductMd(markdown: string): ExtractedDraft {
  const text = markdown.replace(/\r\n/g, "\n");
  const lines = text.split("\n").map((line) => line.trim());
  const heading = lines.find((line) => /^#\s+/.test(line))?.replace(/^#+\s*/, "") ?? "";
  const firstParagraph = lines.find((line) => line.length > 40 && !line.startsWith("#") && !line.startsWith("-")) ?? "";
  const bullets = lines
    .filter((line) => /^[-*]\s+/.test(line))
    .map((line) => line.replace(/^[-*]\s+/, "").trim());

  const productName = heading || findPattern(text, [/product\s*name\s*[:\-]\s*(.+)/i, /name\s*[:\-]\s*(.+)/i]);
  const category = findPattern(text, [/category\s*[:\-]\s*(.+)/i, /domain\s*[:\-]\s*(.+)/i, /industry\s*[:\-]\s*(.+)/i]);
  const audience = findPattern(text, [/target\s+audience\s*[:\-]\s*(.+)/i, /audience\s*[:\-]\s*(.+)/i, /for\s+who\s*[:\-]\s*(.+)/i]);
  const problem = findPattern(text, [/problem\s*[:\-]\s*(.+)/i, /pain\s*points?\s*[:\-]\s*(.+)/i, /challenge\s*[:\-]\s*(.+)/i]);
  const valueProposition = findPattern(text, [/value\s+proposition\s*[:\-]\s*(.+)/i, /promise\s*[:\-]\s*(.+)/i, /solution\s*[:\-]\s*(.+)/i]) || firstParagraph;
  const differentiatorBullets = bullets
    .filter((line) => /feature|differentiator|advantage|benefit|proof|unique/i.test(line))
    .slice(0, 5);
  const differentiators = cleanList((differentiatorBullets.length ? differentiatorBullets : bullets).join("\n"));
  const voiceTone = findPattern(text, [/voice\s*(?:and|&)\s*tone\s*[:\-]\s*(.+)/i, /tone\s*[:\-]\s*(.+)/i, /voice\s*[:\-]\s*(.+)/i]);
  const launchGoal = findPattern(text, [/launch\s+goal\s*[:\-]\s*(.+)/i, /objective\s*[:\-]\s*(.+)/i, /cta\s*[:\-]\s*(.+)/i]);

  const fields = [productName, category, audience, problem, valueProposition, differentiators, voiceTone, launchGoal];
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

function extractionToConfig(extraction: ExtractedDraft): ConfigDraft {
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
      statement: extraction.valueProposition || "Transforms product notes into launch-ready brand assets.",
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

function configToYaml(config: ConfigDraft): string {
  const lines = [
    "brand:",
    `  name: \"${config.brand.name}\"`,
    `  domain: \"${config.brand.domain}\"`,
    `  voice: \"${config.brand.voice}\"`,
    `  tone: \"${config.brand.tone}\"`,
    "audience:",
    `  persona_name: \"${config.audience.personaName}\"`,
    `  pain_points: \"${config.audience.painPoints.replace(/\n/g, " | ")}\"`,
    "positioning:",
    `  statement: \"${config.positioning.statement}\"`,
    "  pillars:",
    ...config.positioning.pillars
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => `    - \"${line}\"`),
    "campaign:",
    `  primary_objective: \"${config.campaign.primaryObjective}\"`,
    "visual:",
    `  palette_mood: \"${config.visual.paletteMood}\"`,
    `  typography: \"${config.visual.typography}\"`,
    `  surface_style: \"${config.visual.surfaceStyle}\"`,
  ];
  return lines.join("\n");
}

function downloadText(fileName: string, content: string, type = "text/plain") {
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

function bytesToHuman(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(input: string): string {
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) return input;
  return date.toLocaleString();
}

function suggestRecovery(message: string): { label: string; steps: string[] } {
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

function buildProcessPages(): ProcessPage[] {
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

function waveForPage(page: ProcessPage): { id: string; label: string } {
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
  if (
    page.kind === "settings" ||
    page.kind === "history" ||
    page.kind === "output-viewer"
  ) {
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

export default function App() {
  const [runState, setRunState] = useState<RunState>("idle");
  const [activeRunnerId, setActiveRunnerId] = useState("bm");
  const [bridgeOnline, setBridgeOnline] = useState(false);
  const [projectName, setProjectName] = useState("brandmint");
  const [brandFolder, setBrandFolder] = useState("./brandmint");
  const [scenario, setScenario] = useState("focused");
  const [waves, setWaves] = useState("1-7");
  const [publishStage, setPublishStage] = useState("notebooklm");
  const [configPath, setConfigPath] = useState("./brand-config.yaml");
  const [productMdPath, setProductMdPath] = useState("./product.md");
  const [productMdText, setProductMdText] = useState("");
  const [extraction, setExtraction] = useState<ExtractedDraft>(emptyExtraction);
  const [extractionConfirmed, setExtractionConfirmed] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [configDraft, setConfigDraft] = useState<ConfigDraft>(defaultConfigDraft());
  const [exportedAt, setExportedAt] = useState("");
  const [lastSavedAt, setLastSavedAt] = useState("");
  const [statusMessage, setStatusMessage] = useState("Ready.");
  const [dryRunMode, setDryRunMode] = useState(false);

  const [bridgeLogs, setBridgeLogs] = useState<BridgeLog[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [references, setReferences] = useState<ReferenceImage[]>([]);
  const [referencesLoading, setReferencesLoading] = useState(false);
  const [selectedReferenceIds, setSelectedReferenceIds] = useState<string[]>([]);
  const [referenceLimit, setReferenceLimit] = useState(30);
  const [refPage, setRefPage] = useState(1);
  const [refPerPage, setRefPerPage] = useState(24);
  const [refSearchQuery, setRefSearchQuery] = useState("");

  const [runners, setRunners] = useState<RunnerInfo[]>(FALLBACK_RUNNERS);
  const [selectedRunner, setSelectedRunner] = useState("bm");
  const [taskPrompt, setTaskPrompt] = useState(DEFAULT_TASK_PROMPT);
  const [taskOutputPath, setTaskOutputPath] = useState("docs/front-ui/generated-update.md");
  const [integrationSettings, setIntegrationSettings] = useState<IntegrationSettings>(DEFAULT_INTEGRATION_SETTINGS);
  const [openrouterApiKeyInput, setOpenrouterApiKeyInput] = useState("");
  const [nbrainApiKeyInput, setNbrainApiKeyInput] = useState("");
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [wikiHandoffDone, setWikiHandoffDone] = useState(false);
  const [astroHandoffDone, setAstroHandoffDone] = useState(false);
  const [logLevelFilter, setLogLevelFilter] = useState<"all" | "info" | "warn" | "error">("all");
  const [compactLogs, setCompactLogs] = useState(false);
  const [showAdvancedLaunch, setShowAdvancedLaunch] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // ── Native App State ──
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>([]);
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([]);
  const [preferences, setPreferences] = useState<AppPreferences>(DEFAULT_PREFERENCES);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [logSearchQuery, setLogSearchQuery] = useState("");
  const [updateAvailable, setUpdateAvailable] = useState<string | null>(null);
  const [pageTransitionKey, setPageTransitionKey] = useState(0);
  const [selectedOutputFile, setSelectedOutputFile] = useState<string | null>(null);
  const [outputViewerData, setOutputViewerData] = useState<Record<string, unknown> | null>(null);
  const [outputCollapsed, setOutputCollapsed] = useState<Record<string, boolean>>({});
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    try { return Number(window.localStorage.getItem("brandmint-sidebar-width")) || 280; } catch { return 280; }
  });
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; pageId: string } | null>(null);
  const runStartTimeRef = useRef<number | null>(null);

  const lastLogIdRef = useRef(0);
  const outputAbortRef = useRef<AbortController | null>(null);

  const processPages = useMemo(() => buildProcessPages(), []);

  const [selectedPageId, setSelectedPageId] = useState(processPages[0]?.id ?? "");
  const [pageSearch, setPageSearch] = useState("");
  const [collapsedWaves, setCollapsedWaves] = useState<Record<string, boolean>>({
    "wave-1": false,
    "wave-2": false,
    "wave-3": false,
    "wave-4": false,
    "wave-5": false,
    "wave-6": false,
    "wave-7": false,
    "wave-8": false,
    "wave-x": false,
  });

  const selectedPage = useMemo(
    () => processPages.find((page) => page.id === selectedPageId) ?? processPages[0],
    [processPages, selectedPageId],
  );

  const selectedPageIndex = useMemo(
    () => Math.max(0, processPages.findIndex((page) => page.id === selectedPage?.id)),
    [processPages, selectedPage?.id],
  );

  const selectedRunnerInfo = useMemo(
    () => runners.find((runner) => runner.id === selectedRunner) ?? FALLBACK_RUNNERS[0],
    [runners, selectedRunner],
  );

  const hasExtraction = useMemo(
    () => Boolean(extraction.productName || extraction.audience || extraction.valueProposition || extraction.differentiators),
    [extraction],
  );

  const synthesisSignals = useMemo(() => {
    const combined = [
      extraction.productName,
      extraction.category,
      extraction.audience,
      extraction.valueProposition,
      extraction.differentiators,
      extraction.voiceTone,
      configDraft.brand.domain,
      configDraft.visual.paletteMood,
      configDraft.visual.typography,
      configDraft.visual.surfaceStyle,
    ].join(" ");
    return Array.from(new Set(tokenize(combined)));
  }, [extraction, configDraft]);

  const rankedReferences = useMemo(() => {
    // Build a searchable text blob for each reference
    const signalSet = new Set(synthesisSignals);

    // Brand-semantic keyword categories with weights
    const semanticBuckets: Record<string, string[]> = {
      branding: ["brand", "logo", "identity", "wordmark", "monogram", "seal", "emblem", "badge"],
      typography: ["typography", "type", "font", "lettering", "serif", "sans", "display", "heading"],
      color: ["palette", "color", "gradient", "swatch", "hue", "tone", "contrast", "scheme"],
      layout: ["layout", "grid", "composition", "bento", "card", "hero", "section", "poster"],
      visual: ["visual", "style", "aesthetic", "mood", "texture", "pattern", "surface", "glass", "morph"],
      product: ["product", "mockup", "packaging", "label", "box", "bottle", "render", "showcase"],
      campaign: ["campaign", "ad", "social", "banner", "story", "reel", "post", "marketing"],
      photography: ["photo", "portrait", "lifestyle", "editorial", "studio", "shot", "film"],
    };

    // Determine which buckets the brand cares about from extraction + config
    const brandText = [
      extraction.productName, extraction.category, extraction.audience,
      extraction.valueProposition, extraction.differentiators, extraction.voiceTone,
      configDraft.brand.domain, configDraft.visual.paletteMood,
      configDraft.visual.typography, configDraft.visual.surfaceStyle,
    ].join(" ").toLowerCase();

    const activeBuckets = new Set<string>();
    for (const [bucket, keywords] of Object.entries(semanticBuckets)) {
      if (keywords.some((kw) => brandText.includes(kw))) activeBuckets.add(bucket);
    }
    // Always activate branding + visual as baseline
    activeBuckets.add("branding");
    activeBuckets.add("visual");

    return references
      .map((ref) => {
        let score = ref.priority; // base: 100 primary, 90 reuse, 75 twitter, 70 alt, 65 style, 55 demo, 40 untagged
        const refTags = new Set(ref.tags.map((tag) => tag.toLowerCase()));
        const refText = `${ref.name} ${ref.description} ${ref.tags.join(" ")}`.toLowerCase();

        // 1. Direct signal→tag match (strongest)
        for (const signal of signalSet) {
          if (refTags.has(signal)) score += 12;
          // Fuzzy: signal appears in name or description
          if (refText.includes(signal)) score += 6;
        }

        // 2. Semantic bucket matching — boost refs that align with brand categories
        for (const [bucket, keywords] of Object.entries(semanticBuckets)) {
          const bucketHits = keywords.filter((kw) => refTags.has(kw) || refText.includes(kw)).length;
          if (bucketHits > 0) {
            const weight = activeBuckets.has(bucket) ? 10 : 3; // much higher for brand-relevant buckets
            score += Math.min(bucketHits, 3) * weight;
          }
        }

        // 3. Source-type boosts
        if (ref.sources.includes("primary")) score += 25;
        if (ref.sources.includes("reuse")) score += 15;
        if (ref.sources.includes("style")) score += 12;
        if (ref.sources.includes("twitter")) score += 8;

        // 4. Asset linkage boost (mapped to actual pipeline assets)
        if (ref.assetIds.length > 0) score += 10 + ref.assetIds.length * 3;

        // 5. Description richness bonus (richer metadata = more curated)
        if (ref.description.length > 20) score += 5;
        if (ref.description.length > 80) score += 5;

        return { ...ref, score };
      })
      .sort((a, b) => b.score - a.score);
  }, [references, synthesisSignals, extraction, configDraft]);

  const topThirtyReferences = useMemo(() => rankedReferences.slice(0, 30), [rankedReferences]);
  const visibleReferences = useMemo(() => rankedReferences.slice(0, referenceLimit), [rankedReferences, referenceLimit]);
  const selectedReferences = useMemo(
    () => rankedReferences.filter((item) => selectedReferenceIds.includes(item.id)),
    [rankedReferences, selectedReferenceIds],
  );

  // Paginated reference library
  const filteredLibraryRefs = useMemo(() => {
    if (!refSearchQuery.trim()) return rankedReferences;
    const q = refSearchQuery.toLowerCase();
    return rankedReferences.filter(
      (r) => r.name.toLowerCase().includes(q) || r.description.toLowerCase().includes(q) || r.tags.some((t) => t.toLowerCase().includes(q)),
    );
  }, [rankedReferences, refSearchQuery]);
  const refTotalPages = Math.max(1, Math.ceil(filteredLibraryRefs.length / refPerPage));
  const paginatedRefs = useMemo(
    () => filteredLibraryRefs.slice((refPage - 1) * refPerPage, refPage * refPerPage),
    [filteredLibraryRefs, refPage, refPerPage],
  );

  const triageCards = useMemo(() => {
    return bridgeLogs
      .filter((log) => log.level === "error")
      .slice(-6)
      .reverse()
      .map((log) => ({ ...suggestRecovery(log.message), id: log.id, message: log.message, at: log.ts }));
  }, [bridgeLogs]);

  const groupedArtifacts = useMemo(() => {
    return artifacts.reduce<Record<string, ArtifactItem[]>>((acc, row) => {
      acc[row.group] = [...(acc[row.group] ?? []), row];
      return acc;
    }, {});
  }, [artifacts]);

  const generatedYaml = useMemo(() => configToYaml(configDraft), [configDraft]);
  const generatedJson = useMemo(() => JSON.stringify(configDraft, null, 2), [configDraft]);

  const pageStatusMap = useMemo<Record<string, PageStatus>>(() => {
    const map: Record<string, PageStatus> = {};
    const errorCount = bridgeLogs.filter((row) => row.level === "error").length;

    for (const page of processPages) {
      let status: PageStatus =
        processPages.findIndex((row) => row.id === page.id) < selectedPageIndex ? "done" : "pending";
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
        status = artifacts.some((row) => row.relativePath.includes("simulated/generated")) ? "done" : "pending";
      } else if (page.kind === "runner-workbench") {
        status = selectedRunner ? "active" : "pending";
      } else if (page.kind === "runner-matrix") {
        status = runners.length ? "done" : "pending";
      } else if (page.kind === "artifacts") {
        status = artifacts.length ? "done" : "pending";
      } else if (page.kind === "handoff") {
        status = exportedAt && selectedReferenceIds.length ? "done" : "pending";
      } else if (page.kind === "publish-notebooklm") {
        const hasNotebookLog = bridgeLogs.some((row) => row.message.toLowerCase().includes("publish:notebooklm"));
        status = activeRunnerId === "publish:notebooklm" && (runState === "running" || runState === "retrying")
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
    artifacts,
    bridgeLogs,
    exportedAt,
    extractionConfirmed,
    hasExtraction,
    pageSearch,
    processPages,
    productMdText,
    references.length,
    runState,
    runners.length,
    integrationSettings.openrouter.hasApiKey,
    activeRunnerId,
    selectedPage?.id,
    selectedPageIndex,
    selectedReferenceIds.length,
    selectedRunner,
    wikiHandoffDone,
    astroHandoffDone,
    wizardStep,
  ]);

  const progressSummary = useMemo(() => {
    const statuses = Object.values(pageStatusMap);
    const done = statuses.filter((row) => row === "done").length;
    const attention = statuses.filter((row) => row === "attention").length;
    const active = statuses.filter((row) => row === "active").length;
    const percent = processPages.length ? Math.round((done / processPages.length) * 100) : 0;
    return { done, attention, active, percent };
  }, [pageStatusMap, processPages.length]);

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

  const filteredBridgeLogs = useMemo(() => {
    if (logLevelFilter === "all") return bridgeLogs;
    return bridgeLogs.filter((row) => row.level === logLevelFilter);
  }, [bridgeLogs, logLevelFilter]);

  const handoffReadiness = useMemo(() => {
    let score = 0;
    if (productMdText.trim().length >= 80) score += 20;
    if (extractionConfirmed) score += 20;
    if (exportedAt) score += 20;
    if (selectedReferenceIds.length >= 6) score += 20;
    if (artifacts.length > 0) score += 20;
    return Math.min(100, score);
  }, [artifacts.length, exportedAt, extractionConfirmed, productMdText, selectedReferenceIds.length]);

  const filteredPages = useMemo(() => {
    const needle = pageSearch.trim().toLowerCase();
    if (!needle) return processPages;
    return processPages.filter((page) => {
      return (
        page.title.toLowerCase().includes(needle) ||
        page.track.toLowerCase().includes(needle) ||
        page.objective.toLowerCase().includes(needle)
      );
    });
  }, [pageSearch, processPages]);

  const waveGroups = useMemo(() => {
    const grouped = filteredPages.reduce<Record<string, WaveGroup>>((acc, page) => {
      const wave = waveForPage(page);
      if (!acc[wave.id]) {
        acc[wave.id] = { id: wave.id, label: wave.label, pages: [] };
      }
      acc[wave.id].pages.push(page);
      return acc;
    }, {});
    const order = ["wave-1", "wave-2", "wave-3", "wave-4", "wave-5", "wave-6", "wave-7", "wave-8", "wave-x"];
    return order.map((id) => grouped[id]).filter(Boolean) as WaveGroup[];
  }, [filteredPages]);

  const commandActions = useMemo<CommandAction[]>(() => {
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
      {
        id: "run-launch",
        label: "Run Launch",
        hint: "Start bm launch",
        run: () => {
          void startRun();
          setCommandPaletteOpen(false);
        },
      },
      {
        id: "open-settings",
        label: "Open Provider Settings",
        hint: "Open model/API config",
        run: () => {
          setSelectedPageId("process-settings");
          setCommandPaletteOpen(false);
        },
      },
      {
        id: "toggle-dry-run",
        label: dryRunMode ? "Disable Dry Run" : "Enable Dry Run",
        hint: "Toggle API simulation mode",
        run: () => {
          setDryRunMode((prev) => !prev);
          setCommandPaletteOpen(false);
        },
      },
      ...pageActions,
    ];
  }, [dryRunMode, processPages]);

  const filteredCommandActions = useMemo(() => {
    const needle = commandQuery.trim().toLowerCase();
    if (!needle) return commandActions.slice(0, 14);
    return commandActions.filter((action) => `${action.label} ${action.hint || ""}`.toLowerCase().includes(needle)).slice(0, 20);
  }, [commandActions, commandQuery]);

  useEffect(() => {
    if (!selectedPage) return;
    const wave = waveForPage(selectedPage);
    setCollapsedWaves((prev) => (prev[wave.id] ? { ...prev, [wave.id]: false } : prev));
  }, [selectedPage]);

  useEffect(() => {
    if (!commandPaletteOpen) setCommandQuery("");
  }, [commandPaletteOpen]);

  // ── Refresh helper for Cmd+R ──
  async function fetchHealth() {
    try {
      const stateRes = await fetch("/api/state");
      if (stateRes.ok) {
        const state = await stateRes.json();
        setBridgeOnline(true);
        if (["idle", "running", "retrying", "aborted"].includes(state.state)) {
          setRunState(state.state as RunState);
        }
      } else {
        setBridgeOnline(false);
      }
      const artRes = await fetch("/api/artifacts?limit=400");
      if (artRes.ok) {
        const data = await artRes.json();
        setArtifacts((data.artifacts || []) as ArtifactItem[]);
      }
      const refRes = await fetch("/api/references?limit=1000");
      if (refRes.ok) {
        const data = await refRes.json();
        setReferences((data.references || []) as ReferenceImage[]);
      }
    } catch {
      setBridgeOnline(false);
      showToast("Bridge unreachable", "error");
    }
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const inField = Boolean(target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT"));

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
        return;
      }
      // #9 Cmd+, for settings
      if ((event.metaKey || event.ctrlKey) && event.key === ",") {
        event.preventDefault();
        setSelectedPageId("process-settings");
        return;
      }
      // #9 Cmd+[ / Cmd+] for prev/next page
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
      // #9 Cmd+B toggle sidebar
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "b") {
        event.preventDefault();
        setSidebarCollapsed((prev) => !prev);
        return;
      }
      // QoL: Cmd+R refresh all data
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "r") {
        event.preventDefault();
        fetchHealth();
        showToast("Refreshing data…", "info");
        return;
      }
      // QoL: Cmd+W close window
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "w") {
        event.preventDefault();
        (async () => {
          try {
            const { getCurrentWindow } = await import("@tauri-apps/api/window");
            getCurrentWindow().close();
          } catch { /* browser fallback: no-op */ }
        })();
        return;
      }
      if (event.key === "Escape") {
        setCommandPaletteOpen(false);
        return;
      }
      if (inField || commandPaletteOpen) return;

      // #9 Arrow key page nav
      if (event.key === "ArrowUp" && selectedPageIndex > 0) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex - 1].id);
      }
      if (event.key === "ArrowDown" && selectedPageIndex < processPages.length - 1) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex + 1].id);
      }
      if (event.key === "ArrowLeft" && selectedPageIndex > 0) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex - 1].id);
      }
      if (event.key === "ArrowRight" && selectedPageIndex < processPages.length - 1) {
        event.preventDefault();
        setSelectedPageId(processPages[selectedPageIndex + 1].id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [commandPaletteOpen, processPages, selectedPageIndex]);

  // QoL: Sidebar resize via drag
  useEffect(() => {
    if (!isResizingSidebar) return;
    const onMove = (e: MouseEvent) => {
      const newWidth = Math.max(200, Math.min(500, e.clientX));
      setSidebarWidth(newWidth);
    };
    const onUp = () => {
      setIsResizingSidebar(false);
      try { window.localStorage.setItem("brandmint-sidebar-width", String(sidebarWidth)); } catch { /* noop */ }
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

  // QoL: Dismiss context menu on click
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

  // QoL: Window position memory
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    (async () => {
      try {
        const { getCurrentWindow } = await import("@tauri-apps/api/window");
        const win = getCurrentWindow();
        const saved = window.localStorage.getItem("brandmint-window-pos");
        if (saved) {
          try {
            const { x, y, w, h } = JSON.parse(saved);
            if (w > 400 && h > 300) {
              win.setPosition(new (await import("@tauri-apps/api/dpi")).LogicalPosition(x, y));
              win.setSize(new (await import("@tauri-apps/api/dpi")).LogicalSize(w, h));
            }
          } catch {
            window.localStorage.removeItem("brandmint-window-pos");
          }
        }
        const savePos = async () => {
          try {
            const pos = await win.outerPosition();
            const size = await win.outerSize();
            window.localStorage.setItem("brandmint-window-pos", JSON.stringify({
              x: pos.x, y: pos.y, w: size.width, h: size.height,
            }));
          } catch { /* noop */ }
        };
        interval = setInterval(savePos, 5000);
      } catch { /* browser mode — no-op */ }
    })();
    return () => { if (interval) clearInterval(interval); };
  }, []);

  useEffect(() => {
    if (!selectedPage && processPages[0]) {
      setSelectedPageId(processPages[0].id);
    }
  }, [processPages, selectedPage]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(DRAFT_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed.projectName) setProjectName(parsed.projectName);
      if (parsed.brandFolder) setBrandFolder(parsed.brandFolder);
      if (parsed.scenario) setScenario(parsed.scenario);
      if (parsed.waves) setWaves(parsed.waves);
      if (parsed.publishStage) setPublishStage(parsed.publishStage);
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
      if (parsed.dryRunMode) setDryRunMode(Boolean(parsed.dryRunMode));
      if (typeof parsed.wikiHandoffDone === "boolean") setWikiHandoffDone(parsed.wikiHandoffDone);
      if (typeof parsed.astroHandoffDone === "boolean") setAstroHandoffDone(parsed.astroHandoffDone);
      setStatusMessage("Draft restored.");
    } catch {
      setStatusMessage("Draft was invalid. Starting fresh.");
    }
  }, []);

  // ── Load run history, recent projects, preferences ──
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

  // ── Save preferences on change ──
  useEffect(() => {
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(preferences)); } catch { /* noop */ }
  }, [preferences]);

  // ── #15 Auto-update check ──
  useEffect(() => {
    const checkUpdate = async () => {
      try {
        const res = await fetch("https://api.github.com/repos/Sheshiyer/brandmint-oracle-aleph/releases/latest", {
          headers: { Accept: "application/vnd.github.v3+json" },
        });
        if (!res.ok) return;
        const data = await res.json();
        const latest = (data.tag_name || "").replace(/^v/, "");
        const current = "4.3.1";
        if (latest && latest !== current && latest > current) {
          setUpdateAvailable(latest);
        }
      } catch { /* noop */ }
    };
    checkUpdate();
  }, []);

  // ── #7 Native file dialog helper ──
  async function openFileDialog(title: string, filters: { name: string; extensions: string[] }[]) {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const result = await open({ title, filters, multiple: false, directory: false });
      return result as string | null;
    } catch {
      return null;
    }
  }

  async function openFolderDialog(title: string) {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const result = await open({ title, multiple: false, directory: true });
      return result as string | null;
    } catch {
      return null;
    }
  }

  // ── #6 Notify on run state changes ──
  const prevRunStateRef = useRef<RunState>("idle");
  useEffect(() => {
    const prev = prevRunStateRef.current;
    prevRunStateRef.current = runState;
    if (prev === "running" && runState === "idle") {
      showToast("Pipeline run completed", "success");
      addRunToHistory("success");
      // #6 Native notification
      (async () => {
        try {
          const { sendNotification } = await import("@tauri-apps/plugin-notification");
          if (preferences.showNotifications) {
            sendNotification({ title: "Brandmint", body: "Pipeline run completed successfully." });
          }
        } catch { /* noop - browser mode */ }
      })();
    } else if (prev === "running" && runState === "aborted") {
      showToast("Pipeline run aborted", "error");
      addRunToHistory("aborted");
    } else if (runState === "running" && prev !== "running") {
      runStartTimeRef.current = Date.now();
      trackRecentProject();
    }
  }, [runState]);

  // ── #11 Page transition trigger ──
  useEffect(() => {
    setPageTransitionKey((prev) => prev + 1);
  }, [selectedPageId]);

  // ── #8 Drag & Drop ──
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
        if (name.endsWith(".yaml") || name.endsWith(".yml")) {
          const reader = new FileReader();
          reader.onload = () => {
            setConfigPath(file.name);
            showToast(`Loaded config: ${file.name}`, "success");
          };
          reader.onerror = () => showToast(`Failed to read ${file.name}`, "error");
          reader.readAsText(file);
        } else if (name.endsWith(".md")) {
          const reader = new FileReader();
          reader.onload = () => {
            setProductMdText(reader.result as string);
            setProductMdPath(file.name);
            showToast(`Loaded product doc: ${file.name}`, "success");
          };
          reader.onerror = () => showToast(`Failed to read ${file.name}`, "error");
          reader.readAsText(file);
        } else if (name.endsWith(".json")) {
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const data = JSON.parse(reader.result as string);
              setOutputViewerData(data);
              setSelectedOutputFile(file.name);
              showToast(`Loaded JSON: ${file.name}`, "info");
            } catch {
              showToast(`Invalid JSON: ${file.name}`, "error");
            }
          };
          reader.onerror = () => showToast(`Failed to read ${file.name}`, "error");
          reader.readAsText(file);
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

  // ── Bridge offline notification ──
  const prevBridgeOnlineRef = useRef(true);
  useEffect(() => {
    if (prevBridgeOnlineRef.current && !bridgeOnline) {
      showToast("Bridge disconnected", "error");
      (async () => {
        try {
          const { sendNotification } = await import("@tauri-apps/plugin-notification");
          if (preferences.showNotifications) {
            sendNotification({ title: "Brandmint", body: "Bridge connection lost." });
          }
        } catch { /* noop */ }
      })();
    } else if (!prevBridgeOnlineRef.current && bridgeOnline) {
      showToast("Bridge reconnected", "success");
    }
    prevBridgeOnlineRef.current = bridgeOnline;
  }, [bridgeOnline]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const timer = setTimeout(() => {
      try {
        const payload = {
          projectName,
          brandFolder,
          scenario,
          waves,
          publishStage,
          configPath,
          productMdPath,
          productMdText,
          extraction,
          extractionConfirmed,
          wizardStep,
          configDraft,
          selectedReferenceIds,
          selectedPageId,
          exportedAt,
          dryRunMode,
          wikiHandoffDone,
          astroHandoffDone,
        };
        window.localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
        setLastSavedAt(new Date().toLocaleTimeString());
      } catch { /* storage full or private mode */ }
    }, 1500);
    return () => clearTimeout(timer);
  }, [
    configDraft,
    brandFolder,
    configPath,
    dryRunMode,
    exportedAt,
    extraction,
    extractionConfirmed,
    productMdPath,
    productMdText,
    projectName,
    publishStage,
    scenario,
    selectedPageId,
    selectedReferenceIds,
    waves,
    wizardStep,
    wikiHandoffDone,
    astroHandoffDone,
  ]);

  function pushLocalLog(level: string, message: string) {
    setBridgeLogs((prev) => [
      ...prev,
      {
        id: Date.now() + Math.floor(Math.random() * 1000),
        ts: new Date().toISOString(),
        level,
        message,
      },
    ]);
  }

  // ── #10 Toast System ──
  function showToast(message: string, kind: Toast["kind"] = "info") {
    const id = Date.now() + Math.floor(Math.random() * 10000);
    setToasts((prev) => [...prev.slice(-4), { id, message, kind }]);
    setTimeout(() => {
      setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 220);
    }, 3500);
  }

  function dismissToast(id: number) {
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 220);
  }

  // ── #5 Run History ──
  function addRunToHistory(status: RunHistoryEntry["status"]) {
    const entry: RunHistoryEntry = {
      id: `run-${Date.now()}`,
      scenario,
      waves,
      startedAt: new Date().toISOString(),
      duration: runStartTimeRef.current ? Math.round((Date.now() - runStartTimeRef.current) / 1000) : 0,
      status,
      projectName,
      configPath,
    };
    setRunHistory((prev) => {
      const next = [entry, ...prev].slice(0, 50);
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); } catch { /* noop */ }
      return next;
    });
    runStartTimeRef.current = null;
  }

  // ── #6 Recent Projects ──
  function trackRecentProject() {
    const proj: RecentProject = { name: projectName, path: brandFolder, lastOpened: new Date().toISOString(), scenario };
    setRecentProjects((prev) => {
      const filtered = prev.filter((p) => p.path !== proj.path);
      const next = [proj, ...filtered].slice(0, 10);
      try { localStorage.setItem(PROJECTS_KEY, JSON.stringify(next)); } catch { /* noop */ }
      return next;
    });
  }

  // ── #12 Output Viewer ──
  function renderJsonTree(data: unknown, depth: number = 0, path: string = "root"): JSX.Element {
    if (data === null) return <span className="json-null">null</span>;
    if (typeof data === "boolean") return <span className="json-boolean">{String(data)}</span>;
    if (typeof data === "number") return <span className="json-number">{data}</span>;
    if (typeof data === "string") {
      const display = data.length > 120 ? data.slice(0, 120) + "..." : data;
      return <span className="json-string">&quot;{display}&quot;</span>;
    }
    if (Array.isArray(data)) {
      const isCollapsed = outputCollapsed[path];
      if (data.length === 0) return <span className="json-bracket">[]</span>;
      return (
        <span>
          <button className="json-toggle" onClick={() => setOutputCollapsed((prev) => ({ ...prev, [path]: !prev[path] }))}>
            {isCollapsed ? "+" : "-"}
          </button>
          <span className="json-bracket">[</span>
          {isCollapsed ? <span className="json-null"> {data.length} items </span> : (
            <div style={{ paddingLeft: 16 }}>
              {data.map((item, i) => (
                <div key={i}>{renderJsonTree(item, depth + 1, `${path}[${i}]`)}{i < data.length - 1 ? "," : ""}</div>
              ))}
            </div>
          )}
          <span className="json-bracket">]</span>
        </span>
      );
    }
    if (typeof data === "object") {
      const entries = Object.entries(data as Record<string, unknown>);
      const isCollapsed = outputCollapsed[path];
      if (entries.length === 0) return <span className="json-bracket">{"{}"}</span>;
      return (
        <span>
          {depth > 0 && (
            <button className="json-toggle" onClick={() => setOutputCollapsed((prev) => ({ ...prev, [path]: !prev[path] }))}>
              {isCollapsed ? "+" : "-"}
            </button>
          )}
          <span className="json-bracket">{"{"}</span>
          {isCollapsed ? <span className="json-null"> {entries.length} keys </span> : (
            <div style={{ paddingLeft: 16 }}>
              {entries.map(([key, val], i) => (
                <div key={key}>
                  <span className="json-key">&quot;{key}&quot;</span>: {renderJsonTree(val, depth + 1, `${path}.${key}`)}
                  {i < entries.length - 1 ? "," : ""}
                </div>
              ))}
            </div>
          )}
          <span className="json-bracket">{"}"}</span>
        </span>
      );
    }
    return <span>{String(data)}</span>;
  }

  // ── #13 Log Search ──
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
    showToast("Logs exported", "success");
  }

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

  async function loadIntegrationSettings() {
    try {
      const res = await fetch("/api/settings");
      if (!res.ok) return;
      const data = await res.json();
      const next = data.settings as IntegrationSettings | undefined;
      if (!next) return;
      setIntegrationSettings((prev) => ({
        openrouter: { ...prev.openrouter, ...(next.openrouter || {}) },
        nbrain: { ...prev.nbrain, ...(next.nbrain || {}) },
        defaults: { ...prev.defaults, ...(next.defaults || {}) },
      }));
      if (next.defaults?.preferredRunner) {
        setSelectedRunner((prev) => (prev === "bm" ? next.defaults.preferredRunner : prev));
      }
    } catch {
      pushLocalLog("warn", "Unable to load provider settings.");
    }
  }

  async function saveIntegrationSettings(options?: { clearOpenrouter?: boolean; clearNbrain?: boolean }) {
    setSettingsSaving(true);
    try {
      const payload: Record<string, unknown> = {
        openrouterModel: integrationSettings.openrouter.model,
        openrouterRouteMode: integrationSettings.openrouter.routeMode,
        openrouterEndpoint: integrationSettings.openrouter.endpoint,
        nbrainEnabled: integrationSettings.nbrain.enabled,
        nbrainModel: integrationSettings.nbrain.model,
        nbrainEndpoint: integrationSettings.nbrain.endpoint,
        preferredRunner: integrationSettings.defaults.preferredRunner,
      };
      if (openrouterApiKeyInput.trim()) {
        payload.openrouterApiKey = openrouterApiKeyInput.trim();
      }
      if (nbrainApiKeyInput.trim()) {
        payload.nbrainApiKey = nbrainApiKeyInput.trim();
      }
      if (options?.clearOpenrouter) {
        payload.clearOpenrouterApiKey = true;
      }
      if (options?.clearNbrain) {
        payload.clearNbrainApiKey = true;
      }

      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "Failed to save settings");
      }
      const data = await res.json();
      const next = data.settings as IntegrationSettings | undefined;
      if (next) {
        setIntegrationSettings({
          openrouter: { ...DEFAULT_INTEGRATION_SETTINGS.openrouter, ...(next.openrouter || {}) },
          nbrain: { ...DEFAULT_INTEGRATION_SETTINGS.nbrain, ...(next.nbrain || {}) },
          defaults: { ...DEFAULT_INTEGRATION_SETTINGS.defaults, ...(next.defaults || {}) },
        });
      }
      const runnersRes = await fetch("/api/runners");
      if (runnersRes.ok) {
        const runnersPayload = await runnersRes.json();
        const catalog = (runnersPayload.runners || []) as RunnerInfo[];
        if (catalog.length) {
          setRunners(catalog);
        }
      }
      setOpenrouterApiKeyInput("");
      setNbrainApiKeyInput("");
      setStatusMessage("Provider settings saved.");
    } catch (error) {
      pushLocalLog("error", `Settings save failed: ${(error as Error).message}`);
    } finally {
      setSettingsSaving(false);
    }
  }

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
          if (state.runner) {
            setActiveRunnerId(String(state.runner));
          }
        } else {
          setBridgeOnline(false);
        }

        const logsRes = await fetch(`/api/logs?since=${lastLogIdRef.current}`);
        if (logsRes.ok) {
          const data = await logsRes.json();
          const incoming: BridgeLog[] = data.logs || [];
          if (incoming.length > 0) {
            setBridgeLogs((prev) => [...prev.slice(-600), ...incoming]);
            lastLogIdRef.current = incoming[incoming.length - 1].id;
          }
        }
      } catch {
        setBridgeOnline(false);
      }
    }, 1500);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const loadArtifacts = async () => {
      try {
        const res = await fetch("/api/artifacts?limit=400");
        if (!res.ok) return;
        const data = await res.json();
        setArtifacts((data.artifacts || []) as ArtifactItem[]);
      } catch {
        // noop
      }
    };

    loadArtifacts();
    const timer = setInterval(loadArtifacts, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const loadReferences = async () => {
      setReferencesLoading(true);
      try {
        const res = await fetch("/api/references?limit=1000");
        if (!res.ok) throw new Error("Failed to load references");
        const data = await res.json();
        setReferences((data.references || []) as ReferenceImage[]);
      } catch {
        pushLocalLog("error", "Unable to load references from /references.");
      } finally {
        setReferencesLoading(false);
      }
    };
    loadReferences();
  }, []);

  useEffect(() => {
    void loadIntegrationSettings();
  }, []);

  useEffect(() => {
    const loadRunners = async () => {
      try {
        const res = await fetch("/api/runners");
        if (!res.ok) return;
        const data = await res.json();
        const catalog = (data.runners || []) as RunnerInfo[];
        if (!catalog.length) {
          setRunners(FALLBACK_RUNNERS);
          return;
        }
        setRunners(catalog);
        setSelectedRunner((current) => {
          const preferred = catalog.find((row) => row.id === current && row.available);
          if (preferred) return current;
          const configured = catalog.find((row) => row.id === integrationSettings.defaults.preferredRunner && row.available);
          const fallback = configured ?? catalog.find((row) => row.available) ?? catalog[0];
          return fallback ? fallback.id : current;
        });
      } catch {
        setRunners(FALLBACK_RUNNERS);
      }
    };

    loadRunners();
  }, [integrationSettings.defaults.preferredRunner]);

  useEffect(() => {
    if (selectedReferenceIds.length || !topThirtyReferences.length) return;
    setSelectedReferenceIds(topThirtyReferences.slice(0, 6).map((row) => row.id));
  }, [selectedReferenceIds.length, topThirtyReferences]);

  function toggleReferenceSelection(id: string) {
    setSelectedReferenceIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  }

  function handleFileUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setProductMdPath(file.name);
    void file.text().then((text) => {
      setProductMdText(text);
      setStatusMessage(`Loaded ${file.name}.`);
    });
  }

  function runExtraction() {
    const trimmed = productMdText.trim();
    if (trimmed.length < 80) {
      setStatusMessage("Product MD is missing/too short. Paste Product MD or load from Brand Folder first.");
      return;
    }
    const parsed = parseProductMd(trimmed);
    setExtraction(parsed);
    setExtractionConfirmed(false);
    setWizardStep(0);
    setStatusMessage(`Extraction complete (${(parsed.confidence * 100).toFixed(0)}% confidence).`);
    setSelectedPageId("process-extraction");
  }

  function confirmExtractionAndBuildWizard() {
    setConfigDraft(extractionToConfig(extraction));
    setExtractionConfirmed(true);
    setWizardStep(0);
    setStatusMessage("Extraction confirmed. Wizard draft generated.");
    setSelectedPageId("process-wizard");
  }

  function loadDemoDryRun() {
    const demoMd = `# BentoPulse\n\nCategory: luxury home fragrance\nTarget Audience: design-aware DTC buyers seeking premium atmosphere\nProblem: Most home fragrance visuals feel generic and not brand-distinct\nValue Proposition: editorial-grade brand system with orchestrated visual outputs in one flow\nDifferentiators:\n- premium bento-grid identity system\n- consistent campaign visuals from one config\n- guided workflow for non-technical operators\nVoice and Tone: elegant, calm, modern\nLaunch Goal: build premium launch assets and start conversion campaign\n`;
    const parsed = parseProductMd(demoMd);
    const draft = extractionToConfig(parsed);

    setDryRunMode(true);
    setBrandFolder("./demo-brand");
    setProductMdPath("./demo-product.md");
    setProductMdText(demoMd);
    setExtraction(parsed);
    setExtractionConfirmed(true);
    setConfigDraft(draft);
    setWizardStep(4);
    setConfigPath("./brand-config.demo.yaml");
    setExportedAt(new Date().toLocaleString());
    setStatusMessage("Dry-run data loaded.");
    setSelectedPageId("process-launch");
    pushLocalLog("info", "[dry-run] Demo data prefilled for multi-process walkthrough.");
  }

  function clearDraft() {
    try { window.localStorage.removeItem(DRAFT_KEY); } catch { /* noop */ }
    setProjectName("brandmint");
    setBrandFolder("./brandmint");
    setScenario("focused");
    setWaves("1-7");
    setPublishStage("notebooklm");
    setConfigPath("./brand-config.yaml");
    setProductMdPath("./product.md");
    setProductMdText("");
    setExtraction(emptyExtraction);
    setExtractionConfirmed(false);
    setWizardStep(0);
    setConfigDraft(defaultConfigDraft());
    setExportedAt("");
    setSelectedReferenceIds([]);
    setWikiHandoffDone(false);
    setAstroHandoffDone(false);
    setStatusMessage("Draft cleared.");
  }

  async function loadFromBrandFolder() {
    if (!brandFolder.trim()) {
      setStatusMessage("Enter a brand folder first.");
      return;
    }
    try {
      const result = await postJson("/api/intake/load", {
        brandFolder: brandFolder.trim(),
        productMdFile: "product.md",
        configFile: "brand-config.yaml",
      });
      if (result?.brandFolder) {
        setBrandFolder(String(result.brandFolder));
      }
      if (result?.productMdPath) {
        setProductMdPath(String(result.productMdPath));
      }
      if (typeof result?.productMdText === "string" && result.productMdText.trim()) {
        setProductMdText(result.productMdText);
      }
      if (result?.configPath) {
        setConfigPath(String(result.configPath));
      }
      const warnings = (result?.warnings || []) as string[];
      if (warnings.length) {
        pushLocalLog("warn", warnings.join(" | "));
      }
      setStatusMessage("Loaded intake context from brand folder.");
    } catch (error) {
      pushLocalLog("error", `Brand folder load failed: ${(error as Error).message}`);
    }
  }

  function exportConfigFiles() {
    const yamlPathName = configPath.split("/").pop() || "brand-config.yaml";
    const jsonPathName = yamlPathName.replace(/\.ya?ml$/i, ".json");
    downloadText(yamlPathName, generatedYaml, "text/yaml");
    downloadText(jsonPathName, generatedJson, "application/json");
    setExportedAt(new Date().toLocaleString());
    setStatusMessage("Config exported (YAML + JSON).");
  }

  function generateSelectedReferencesDryRun() {
    if (!selectedReferences.length) {
      setStatusMessage("Select at least one reference first.");
      return;
    }
    if (!dryRunMode) {
      setStatusMessage("Enable Dry Run mode to simulate FAL generation without API calls.");
      return;
    }

    pushLocalLog("info", `[dry-run] Simulating FAL generation for ${selectedReferences.length} selected references.`);
    const simulated = selectedReferences.slice(0, 12).map((ref, idx) => ({
      name: `generated-${idx + 1}-${ref.name}`,
      path: ref.relativePath,
      relativePath: `simulated/generated/${ref.name}`,
      size: Math.max(ref.size, 85000),
      modifiedAt: new Date().toISOString(),
      extension: ".png",
      group: "deliverables",
    }));

    setArtifacts((prev) => [...simulated, ...prev].slice(0, 400));
    setStatusMessage(`Dry-run queued ${simulated.length} visual outputs.`);
  }

  async function startRun() {
    try {
      await postJson("/api/run/start", {
        runner: "bm",
        brandFolder,
        configPath,
        scenario,
        waves,
      });
      setStatusMessage("Launch started.");
    } catch (error) {
      pushLocalLog("error", `Start failed: ${(error as Error).message}`);
    }
  }

  async function retryRun() {
    try {
      await postJson("/api/run/retry", {
        runner: "bm",
        brandFolder,
        configPath,
        scenario,
        waves,
      });
      setStatusMessage("Retry started with fixed port policy.");
    } catch (error) {
      pushLocalLog("error", `Retry failed: ${(error as Error).message}`);
    }
  }

  async function startPublishStage(stageOverride?: string) {
    const stage = stageOverride || publishStage;
    try {
      await postJson("/api/publish/start", {
        stage,
        configPath,
      });
      setStatusMessage(`Publish stage '${stage}' started.`);
    } catch (error) {
      pushLocalLog("error", `Publish failed: ${(error as Error).message}`);
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

  async function runTaskWithRunner() {
    if (!selectedRunnerInfo?.available) {
      pushLocalLog("error", `Runner '${selectedRunner}' is unavailable in this environment.`);
      return;
    }
    if (selectedRunner === "openrouter" && !integrationSettings.openrouter.hasApiKey) {
      pushLocalLog("warn", "OpenRouter API key is missing. Configure it in Provider Settings.");
      setSelectedPageId("process-settings");
      return;
    }
    if (selectedRunner === "nbrain") {
      if (!integrationSettings.nbrain.hasApiKey) {
        pushLocalLog("warn", "NBrain API key is missing. Configure it in Provider Settings.");
        setSelectedPageId("process-settings");
        return;
      }
      if (!integrationSettings.nbrain.endpoint.trim()) {
        pushLocalLog("warn", "NBrain endpoint is missing. Configure it in Provider Settings.");
        setSelectedPageId("process-settings");
        return;
      }
    }
    if (selectedRunnerInfo.requiresPrompt && !taskPrompt.trim()) {
      pushLocalLog("warn", "Task prompt is required for selected runner.");
      return;
    }
    try {
      const model =
        selectedRunner === "openrouter"
          ? integrationSettings.openrouter.model
          : selectedRunner === "nbrain"
            ? integrationSettings.nbrain.model
            : undefined;
      const endpoint =
        selectedRunner === "openrouter"
          ? integrationSettings.openrouter.endpoint
          : selectedRunner === "nbrain"
            ? integrationSettings.nbrain.endpoint
            : undefined;

      const result = await postJson("/api/run/start", {
        runner: selectedRunner,
        brandFolder,
        configPath,
        scenario,
        waves,
        taskPrompt,
        outputPath: taskOutputPath,
        model,
        endpoint,
      });
      if (result?.runner) {
        pushLocalLog("info", `Runner '${result.runner}' started successfully.`);
      }
    } catch (error) {
      pushLocalLog("error", `Runner start failed: ${(error as Error).message}`);
    }
  }

  function renderWizardPane() {
    switch (wizardStep) {
      case 0:
        return (
          <div className="page-form-grid">
            <label className="field">
              Brand name
              <input
                value={configDraft.brand.name}
                onChange={(e) => setConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, name: e.target.value } }))}
              />
            </label>
            <label className="field">
              Domain / category
              <input
                value={configDraft.brand.domain}
                onChange={(e) => setConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, domain: e.target.value } }))}
              />
            </label>
          </div>
        );
      case 1:
        return (
          <div className="page-form-grid">
            <label className="field">
              Persona
              <input
                value={configDraft.audience.personaName}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, audience: { ...prev.audience, personaName: e.target.value } }))
                }
              />
            </label>
            <label className="field">
              Pain points
              <textarea
                className="field-textarea short"
                value={configDraft.audience.painPoints}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, audience: { ...prev.audience, painPoints: e.target.value } }))
                }
              />
            </label>
          </div>
        );
      case 2:
        return (
          <div className="page-form-grid">
            <label className="field">
              Voice
              <input
                value={configDraft.brand.voice}
                onChange={(e) => setConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, voice: e.target.value } }))}
              />
            </label>
            <label className="field">
              Tone
              <input
                value={configDraft.brand.tone}
                onChange={(e) => setConfigDraft((prev) => ({ ...prev, brand: { ...prev.brand, tone: e.target.value } }))}
              />
            </label>
          </div>
        );
      case 3:
        return (
          <div className="page-form-grid">
            <label className="field">
              Palette mood
              <input
                value={configDraft.visual.paletteMood}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, paletteMood: e.target.value } }))
                }
              />
            </label>
            <label className="field">
              Typography
              <input
                value={configDraft.visual.typography}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, typography: e.target.value } }))
                }
              />
            </label>
            <label className="field">
              Surface style
              <input
                value={configDraft.visual.surfaceStyle}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, visual: { ...prev.visual, surfaceStyle: e.target.value } }))
                }
              />
            </label>
          </div>
        );
      case 4:
      default:
        return (
          <div className="page-form-grid">
            <label className="field">
              Positioning statement
              <textarea
                className="field-textarea short"
                value={configDraft.positioning.statement}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, positioning: { ...prev.positioning, statement: e.target.value } }))
                }
              />
            </label>
            <label className="field">
              Positioning pillars (line separated)
              <textarea
                className="field-textarea short"
                value={configDraft.positioning.pillars}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, positioning: { ...prev.positioning, pillars: e.target.value } }))
                }
              />
            </label>
            <label className="field">
              Campaign objective
              <input
                value={configDraft.campaign.primaryObjective}
                onChange={(e) =>
                  setConfigDraft((prev) => ({ ...prev, campaign: { ...prev.campaign, primaryObjective: e.target.value } }))
                }
              />
            </label>
          </div>
        );
    }
  }

  function renderEmptyState(title: string, description: string, actionLabel?: string, action?: () => void) {
    return (
      <article className="empty-state">
        <h4>{title}</h4>
        <p>{description}</p>
        {actionLabel && action && (
          <button className="btn" onClick={action}>
            {actionLabel}
          </button>
        )}
      </article>
    );
  }

  function renderReferenceSkeleton(count = 8) {
    return (
      <div className="reference-grid-modern">
        {Array.from({ length: count }).map((_, idx) => (
          <article key={`sk-${idx}`} className="reference-card-modern skeleton-card">
            <div className="skeleton-thumb" />
            <div className="skeleton-body">
              <div className="skeleton-line lg" />
              <div className="skeleton-line md" />
              <div className="skeleton-line sm" />
            </div>
          </article>
        ))}
      </div>
    );
  }

  function renderReferenceGrid(rows: Array<ReferenceImage & { score?: number }>) {
    return (
      <div className="reference-grid-modern">
        {rows.map((ref) => {
          const selected = selectedReferenceIds.includes(ref.id);
          return (
            <article
              key={ref.id}
              className={`reference-card-modern ${selected ? "selected" : ""}`}
              onClick={() => toggleReferenceSelection(ref.id)}
              onMouseMove={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
                event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.removeProperty("--mx");
                event.currentTarget.style.removeProperty("--my");
              }}
            >
              <div className="scan-lines" />
              <div className="glitch-line" />
              <img src={ref.url} alt={ref.name} loading="lazy" />
              <div>
                <h4>{ref.name}</h4>
                <p>{ref.description || ref.relativePath}</p>
                <div className="chip-row">
                  {typeof ref.score === "number" && <span>score {Math.round(ref.score)}</span>}
                  {ref.assetIds.slice(0, 2).map((asset) => (
                    <span key={`${ref.id}-${asset}`}>asset {asset}</span>
                  ))}
                  {ref.tags.slice(0, 3).map((tag) => (
                    <span key={`${ref.id}-${tag}`}>{tag}</span>
                  ))}
                </div>
              </div>
              <div className="hover-details">
                <div className="detail-row"><span className="detail-label">Score</span><span className="detail-value">{typeof ref.score === "number" ? Math.round(ref.score) : "n/a"}</span></div>
                <div className="detail-row"><span className="detail-label">Source</span><span className="detail-value">{ref.sources[0] || "library"}</span></div>
                <div className="detail-row"><span className="detail-label">Asset IDs</span><span className="detail-value">{ref.assetIds.length || 0}</span></div>
              </div>
              <input
                type="checkbox"
                checked={selected}
                onChange={() => toggleReferenceSelection(ref.id)}
                onClick={(e) => e.stopPropagation()}
              />
            </article>
          );
        })}
      </div>
    );
  }

  function renderProcessPage(page: ProcessPage) {
    switch (page.kind) {
      case "journey":
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
            <aside
              className="journey-right"
              onMouseMove={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
                event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.removeProperty("--mx");
                event.currentTarget.style.removeProperty("--my");
              }}
            >
              <div className="scan-lines" />
              <div className="glitch-line" />
              <div className="overlay-ui">
                <span className="ui-badge">LIVE SURFACE</span>
                <span className="ui-coords">PAGE::{selectedPageIndex + 1} / {processPages.length}</span>
              </div>
              <div className="mesh-gallery">
                {page.focus.slice(0, 3).map((item, idx) => (
                  <div key={`${page.id}-mesh-${item}`} className="mesh-card">
                    <div className={`wireframe-mesh mesh-shape-${idx + 1}`}>
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

      case "intake":
        return (
          <section className="content-block priority-block">
            <h3>Product MD Intake</h3>
            <p>Start here. If Product MD is not provided, set the brand folder and load `product.md` from it.</p>
            <label className="field">
              Brand folder
              <div style={{ display: "flex", gap: 8 }}>
                <input style={{ flex: 1 }} value={brandFolder} onChange={(e) => setBrandFolder(e.target.value)} placeholder="./my-brand" />
                <button className="btn" onClick={async () => { const f = await openFolderDialog("Select brand folder"); if (f) { setBrandFolder(f); showToast(`Brand folder: ${f}`, "success"); } }}>Browse</button>
              </div>
            </label>
            <div className="controls-row">
              <input type="file" accept=".md,.txt" onChange={handleFileUpload} />
              <button className="btn" onClick={() => void loadFromBrandFolder()}>Load From Brand Folder</button>
              <button className="btn" onClick={async () => { const f = await openFileDialog("Select product.md", [{ name: "Markdown", extensions: ["md", "txt"] }]); if (f) { setProductMdPath(f); showToast(`Product doc: ${f}`, "info"); } }}>Open File</button>
              <button className="btn" onClick={loadDemoDryRun}>Load Demo Dry Run</button>
              <button className="btn" onClick={clearDraft}>Clear Draft</button>
            </div>
            <label className="field">
              Source path
              <input value={productMdPath} onChange={(e) => setProductMdPath(e.target.value)} />
            </label>
            <label className="field">
              Product MD content
              <textarea className="field-textarea" value={productMdText} onChange={(e) => setProductMdText(e.target.value)} />
              <small className={`field-hint ${productMdText.trim().length > 0 && productMdText.trim().length < 80 ? "warn" : ""}`}>
                {productMdText.trim().length}/80 minimum chars for stable extraction.
              </small>
            </label>
            <div className="controls-row">
              <button className="btn btn-primary" onClick={runExtraction}>Run Extraction</button>
            </div>
          </section>
        );

      case "extraction":
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
                <input value={extraction.productName} onChange={(e) => setExtraction((prev) => ({ ...prev, productName: e.target.value }))} />
              </label>
              <label className="field">
                Category
                <input value={extraction.category} onChange={(e) => setExtraction((prev) => ({ ...prev, category: e.target.value }))} />
              </label>
              <label className="field">
                Audience
                <input value={extraction.audience} onChange={(e) => setExtraction((prev) => ({ ...prev, audience: e.target.value }))} />
              </label>
              <label className="field">
                Problem
                <textarea className="field-textarea short" value={extraction.problem} onChange={(e) => setExtraction((prev) => ({ ...prev, problem: e.target.value }))} />
              </label>
              <label className="field">
                Value proposition
                <textarea className="field-textarea short" value={extraction.valueProposition} onChange={(e) => setExtraction((prev) => ({ ...prev, valueProposition: e.target.value }))} />
              </label>
              <label className="field">
                Differentiators
                <textarea className="field-textarea short" value={extraction.differentiators} onChange={(e) => setExtraction((prev) => ({ ...prev, differentiators: e.target.value }))} />
              </label>
              <label className="field">
                Voice and tone
                <input value={extraction.voiceTone} onChange={(e) => setExtraction((prev) => ({ ...prev, voiceTone: e.target.value }))} />
              </label>
              <label className="field">
                Launch goal
                <input value={extraction.launchGoal} onChange={(e) => setExtraction((prev) => ({ ...prev, launchGoal: e.target.value }))} />
              </label>
            </div>
            <div className="controls-row">
              <button className="btn btn-primary" onClick={confirmExtractionAndBuildWizard}>Confirm and Continue</button>
            </div>
          </section>
        );

      case "wizard":
        return (
          <section className="content-block">
            <h3>Brand Config Wizard</h3>
            <div className="wizard-rail-modern">
              {[
                "Brand Basics",
                "Audience",
                "Voice",
                "Visual",
                "Review",
              ].map((label, idx) => (
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
              <button className="btn" onClick={() => setWizardStep((prev) => Math.max(0, prev - 1))}>Prev</button>
              <button className="btn" onClick={() => setWizardStep((prev) => Math.min(4, prev + 1))}>Next</button>
              <button className="btn btn-primary" onClick={() => setSelectedPageId("process-export")}>Go to Export</button>
            </div>
          </section>
        );

      case "export":
        return (
          <section className="content-block">
            <h3>Config Export</h3>
            <label className="field">
              Config path
              <input value={configPath} onChange={(e) => setConfigPath(e.target.value)} />
            </label>
            <div className="controls-row">
              <button className="btn btn-primary" onClick={exportConfigFiles}>Export YAML + JSON</button>
            </div>
            <pre className="code-preview">{generatedYaml}</pre>
          </section>
        );

      case "launch":
        return (
          <section className="content-block priority-block">
            <h3>Launch Controls</h3>
            <div className="metric-grid">
              <article className="metric-card">
                <span>Journey completion</span>
                <strong>{progressSummary.percent}%</strong>
              </article>
              <article className="metric-card">
                <span>Pages done</span>
                <strong>{progressSummary.done} / {processPages.length}</strong>
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
            <div className="progress-strip" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progressSummary.percent}>
              <div className="progress-fill" style={{ width: `${progressSummary.percent}%` }} />
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
                <input value={configPath} onChange={(e) => setConfigPath(e.target.value)} />
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
              <button className="btn" onClick={() => setShowAdvancedLaunch((prev) => !prev)}>
                {showAdvancedLaunch ? "Hide Advanced" : "More Options"}
              </button>
            </div>
            {showAdvancedLaunch && (
              <div className="content-block nested-block">
              <h4>Publishing controls</h4>
              <p>
                Wave 7 covers NotebookLM/Decks/Reports/Diagrams/Video. Wiki docs + Astro builder are post-pipeline steps.
              </p>
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

      case "activity":
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
              {!searchFilteredLogs.length && renderEmptyState("No logs match", "Try a different filter or search term.")}
            </div>
          </section>
        );

      case "triage":
        return (
          <section className="content-block">
            <h3>Failure Triage</h3>
            <div className="list-grid">
              {triageCards.length ? (
                triageCards.map((card) => (
                  <article className="list-card" key={card.id}>
                    <h4>{card.label}</h4>
                    <p>{card.message}</p>
                    <small>{formatTime(card.at)}</small>
                    <ul>
                      {card.steps.map((step) => (
                        <li key={`${card.id}-${step}`}>{step}</li>
                      ))}
                    </ul>
                  </article>
                ))
              ) : (
                renderEmptyState("No active failures", "When errors show up in the activity stream, recovery cards appear here.")
              )}
            </div>
          </section>
        );

      case "settings":
        return (
          <>
            {/* Appearance Section */}
            <div className="settings-section">
              <h4>Appearance</h4>
              <div className="settings-row">
                <div>
                  <div className="settings-row-label">Notifications</div>
                  <div className="settings-row-desc">Show native OS notifications for run events</div>
                </div>
                <div className="settings-row-control">
                  <select value={preferences.showNotifications ? "on" : "off"} onChange={(e) => setPreferences((prev) => ({ ...prev, showNotifications: e.target.value === "on" }))}>
                    <option value="on">On</option>
                    <option value="off">Off</option>
                  </select>
                </div>
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row-label">Auto-save drafts</div>
                  <div className="settings-row-desc">Automatically persist work to local storage</div>
                </div>
                <div className="settings-row-control">
                  <select value={preferences.autoSave ? "on" : "off"} onChange={(e) => setPreferences((prev) => ({ ...prev, autoSave: e.target.value === "on" }))}>
                    <option value="on">On</option>
                    <option value="off">Off</option>
                  </select>
                </div>
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row-label">Log retention</div>
                  <div className="settings-row-desc">Maximum number of log entries to keep in memory</div>
                </div>
                <div className="settings-row-control">
                  <select value={preferences.logRetention} onChange={(e) => setPreferences((prev) => ({ ...prev, logRetention: Number(e.target.value) }))}>
                    <option value="200">200</option>
                    <option value="500">500</option>
                    <option value="1000">1000</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Recent Projects */}
            {recentProjects.length > 0 && (
              <div className="settings-section">
                <h4>Recent Projects</h4>
                <div className="project-grid">
                  {recentProjects.map((proj) => (
                    <div key={proj.path} className="project-card" onClick={() => { setBrandFolder(proj.path); setProjectName(proj.name); setScenario(proj.scenario); showToast(`Loaded project: ${proj.name}`, "info"); }}>
                      <h4>{proj.name}</h4>
                      <p>{proj.path}</p>
                      <p style={{ marginTop: 4 }}>{proj.scenario} &middot; {new Date(proj.lastOpened).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Provider Integrations */}
            <div className="settings-section">
              <h4>Provider Integrations</h4>
              <div className="metric-grid">
                <article className="metric-card">
                  <span>OpenRouter key</span>
                  <strong>{integrationSettings.openrouter.hasApiKey ? integrationSettings.openrouter.apiKeyMasked : "not set"}</strong>
                </article>
                <article className="metric-card">
                  <span>OpenRouter model</span>
                  <strong>{integrationSettings.openrouter.model}</strong>
                </article>
                <article className="metric-card">
                  <span>NBrain key</span>
                  <strong>{integrationSettings.nbrain.hasApiKey ? integrationSettings.nbrain.apiKeyMasked : "not set"}</strong>
                </article>
                <article className="metric-card">
                  <span>Preferred runner</span>
                  <strong>{integrationSettings.defaults.preferredRunner}</strong>
                </article>
              </div>
              <div className="page-form-grid">
                <label className="field">
                  OpenRouter API key
                  <input type="password" value={openrouterApiKeyInput} onChange={(e) => setOpenrouterApiKeyInput(e.target.value)} placeholder={integrationSettings.openrouter.hasApiKey ? "set new to rotate" : "sk-or-v1-..."} />
                </label>
                <label className="field">
                  OpenRouter model
                  <input value={integrationSettings.openrouter.model} onChange={(e) => setIntegrationSettings((prev) => ({ ...prev, openrouter: { ...prev.openrouter, model: e.target.value } }))} />
                </label>
                <label className="field">
                  Model router mode
                  <select value={integrationSettings.openrouter.routeMode} onChange={(e) => setIntegrationSettings((prev) => ({ ...prev, openrouter: { ...prev.openrouter, routeMode: e.target.value } }))}>
                    <option value="balanced">balanced</option>
                    <option value="quality">quality</option>
                    <option value="speed">speed</option>
                  </select>
                </label>
                <label className="field">
                  Preferred runner
                  <select value={integrationSettings.defaults.preferredRunner} onChange={(e) => setIntegrationSettings((prev) => ({ ...prev, defaults: { ...prev.defaults, preferredRunner: e.target.value } }))}>
                    {runners.map((runner) => (<option key={runner.id} value={runner.id}>{runner.label}</option>))}
                  </select>
                </label>
              </div>
              <div className="controls-row">
                <button className="btn btn-primary" onClick={() => { void saveIntegrationSettings(); showToast("Settings saved", "success"); }} disabled={settingsSaving}>{settingsSaving ? "Saving..." : "Save Settings"}</button>
                <button className="btn" onClick={() => void loadIntegrationSettings()}>Reload</button>
                <button className="btn btn-danger" onClick={() => void saveIntegrationSettings({ clearOpenrouter: true })}>Clear OpenRouter Key</button>
              </div>
            </div>

            {/* About */}
            <div className="settings-section">
              <h4>About</h4>
              <div className="settings-row">
                <div>
                  <div className="settings-row-label">Version</div>
                  <div className="settings-row-desc">Brandmint Desktop v4.3.1</div>
                </div>
                {updateAvailable && <span className="update-badge" onClick={() => window.open("https://github.com/Sheshiyer/brandmint-oracle-aleph/releases/latest", "_blank")}>v{updateAvailable} available</span>}
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row-label">Keyboard shortcuts</div>
                  <div className="settings-row-desc">Cmd+K command palette &middot; Cmd+, settings &middot; Cmd+B sidebar &middot; Cmd+[/] prev/next &middot; Arrows navigate</div>
                </div>
              </div>
            </div>
          </>
        );

      case "history":
        return (
          <section className="content-block">
            <h3>Run History</h3>
            <p>Past pipeline runs stored locally on this machine.</p>
            {runHistory.length === 0 ? (
              renderEmptyState("No runs yet", "Start a pipeline run and it will appear here.")
            ) : (
              <div className="history-list">
                {runHistory.map((entry) => (
                  <div key={entry.id} className={`history-card ${entry.status}`}>
                    <div>
                      <p className="history-title">{entry.projectName} &middot; {entry.scenario}</p>
                      <p className="history-subtitle">Waves {entry.waves} &middot; {entry.duration > 0 ? `${Math.floor(entry.duration / 60)}m ${entry.duration % 60}s` : "< 1s"}</p>
                    </div>
                    <div className="history-meta">
                      <span>{entry.status}</span>
                      <span>{new Date(entry.startedAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {runHistory.length > 0 && (
              <div className="controls-row">
                <button className="btn btn-danger" onClick={() => { setRunHistory([]); try { localStorage.removeItem(HISTORY_KEY); } catch { /* noop */ } showToast("History cleared", "info"); }}>Clear History</button>
              </div>
            )}
          </section>
        );

      case "output-viewer":
        return (
          <section className="content-block">
            <h3>Output Viewer</h3>
            <p>Inspect pipeline skill outputs as collapsible JSON trees.</p>
            <div className="controls-row">
              {artifacts.filter((a) => a.extension === ".json" && a.group === "outputs").map((art) => (
                <button key={art.name} className={`btn ${selectedOutputFile === art.name ? "btn-primary" : ""}`} onClick={async () => {
                  if (outputAbortRef.current) outputAbortRef.current.abort();
                  const controller = new AbortController();
                  outputAbortRef.current = controller;
                  setSelectedOutputFile(art.name);
                  try {
                    const res = await fetch(`/api/artifacts/read?path=${encodeURIComponent(art.relativePath)}`, { signal: controller.signal });
                    if (controller.signal.aborted) return;
                    if (res.ok) {
                      const data = await res.json();
                      setOutputViewerData(data);
                      setOutputCollapsed({});
                    } else {
                      showToast(`Failed to load ${art.name}`, "error");
                    }
                  } catch (err) {
                    if ((err as Error).name === "AbortError") return;
                    showToast(`Failed to load ${art.name}`, "error");
                  }
                }}>{art.name.replace(".json", "")}</button>
              ))}
              <button className="btn" onClick={async () => {
                const f = await openFileDialog("Open JSON output", [{ name: "JSON", extensions: ["json"] }]);
                if (f) { setSelectedOutputFile(f); showToast(`Selected: ${f}`, "info"); }
              }}>Open File</button>
            </div>
            {outputViewerData ? (
              <div className="output-viewer" style={{ marginTop: 12 }}>
                <div className="output-viewer-header">
                  <h4>{selectedOutputFile}</h4>
                  <button className="btn" onClick={() => { setOutputCollapsed({}); }}>Expand All</button>
                </div>
                <div className="json-tree">{renderJsonTree(outputViewerData)}</div>
              </div>
            ) : (
              renderEmptyState("No output selected", "Click an output file above or drop a JSON file into the window.")
            )}
          </section>
        );

      case "reference-curation": {
        const topScore = topThirtyReferences[0]?.score ?? 0;
        const hasSignals = synthesisSignals.length > 0;
        return (
          <section className="content-block">
            <h3>Reference Curation — Top 30</h3>
            <p style={{ color: "var(--fg-secondary)", fontSize: 13, margin: "0 0 12px" }}>
              {hasSignals
                ? `Ranked by semantic match to brand signals (${synthesisSignals.slice(0, 6).join(", ")}${synthesisSignals.length > 6 ? "…" : ""}). Top score: ${topScore}.`
                : "Fill in Product MD Intake or Brand Config to activate semantic ranking. Currently sorted by source priority."}
            </p>
            <div className="controls-row">
              <button className="btn" onClick={() => setSelectedReferenceIds(topThirtyReferences.map((row) => row.id))}>Select Top 30</button>
              <button className="btn" onClick={() => setSelectedReferenceIds([])}>Clear Selection</button>
              <span className="status-chip">selected {selectedReferenceIds.length}</span>
              <span className="status-chip">{references.length} total assets</span>
            </div>
            {referencesLoading
              ? renderReferenceSkeleton(10)
              : topThirtyReferences.length
                ? renderReferenceGrid(topThirtyReferences)
                : renderEmptyState("No references found", "Add references to /references and refresh this page.")}
          </section>
        );
      }

      case "reference-library": {
        const pageNumbers: number[] = [];
        const maxVisible = 7;
        if (refTotalPages <= maxVisible) {
          for (let i = 1; i <= refTotalPages; i++) pageNumbers.push(i);
        } else {
          pageNumbers.push(1);
          const start = Math.max(2, refPage - 1);
          const end = Math.min(refTotalPages - 1, refPage + 1);
          if (start > 2) pageNumbers.push(-1); // ellipsis
          for (let i = start; i <= end; i++) pageNumbers.push(i);
          if (end < refTotalPages - 1) pageNumbers.push(-2); // ellipsis
          pageNumbers.push(refTotalPages);
        }
        return (
          <section className="content-block">
            <h3>Reference Library</h3>

            {/* Search + per-page controls */}
            <div className="ref-toolbar">
              <input
                className="ref-search-input"
                value={refSearchQuery}
                onChange={(e) => { setRefSearchQuery(e.target.value); setRefPage(1); }}
                placeholder="Search by name, tag, or description…"
              />
              <span className="status-chip">{filteredLibraryRefs.length} assets</span>
              <select className="ref-per-page" value={refPerPage} onChange={(e) => { setRefPerPage(Number(e.target.value)); setRefPage(1); }}>
                <option value={12}>12 / page</option>
                <option value={24}>24 / page</option>
                <option value={48}>48 / page</option>
                <option value={96}>96 / page</option>
              </select>
            </div>

            {/* Grid */}
            {referencesLoading
              ? renderReferenceSkeleton(refPerPage)
              : paginatedRefs.length
                ? renderReferenceGrid(paginatedRefs)
                : renderEmptyState("No matches", "Try a different search query.")}

            {/* Pagination bar */}
            {refTotalPages > 1 && (
              <div className="ref-pagination">
                <button className="ref-page-btn" disabled={refPage <= 1} onClick={() => setRefPage((p) => p - 1)}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                {pageNumbers.map((n, i) =>
                  n < 0 ? (
                    <span key={`ell-${i}`} className="ref-page-ellipsis">&hellip;</span>
                  ) : (
                    <button key={n} className={`ref-page-btn${n === refPage ? " active" : ""}`} onClick={() => setRefPage(n)}>{n}</button>
                  ),
                )}
                <button className="ref-page-btn" disabled={refPage >= refTotalPages} onClick={() => setRefPage((p) => p + 1)}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
                <span className="ref-page-info">Page {refPage} of {refTotalPages}</span>
              </div>
            )}
          </section>
        );
      }

      case "fal-dry-run":
        return (
          <section className="content-block">
            <h3>FAL Selection Dry Run</h3>
            <p>Simulates generation from selected references without API calls.</p>
            <div className="controls-row">
              <button className="btn btn-primary" onClick={generateSelectedReferencesDryRun}>Simulate Generation</button>
              <button className={`btn ${dryRunMode ? "btn-primary" : ""}`} onClick={() => setDryRunMode((prev) => !prev)}>
                {dryRunMode ? "Dry Run Enabled" : "Enable Dry Run"}
              </button>
            </div>
            <div className="chip-row">
              {selectedReferences.slice(0, 20).map((ref) => (
                <span key={ref.id}>{ref.name}</span>
              ))}
            </div>
          </section>
        );

      case "runner-workbench":
        return (
          <section className="content-block">
            <h3>Runner Workbench</h3>
            <div className="chip-row">
              <span>{selectedRunnerInfo?.description || "Runner ready"}</span>
              {selectedRunner === "openrouter" && <span>model {integrationSettings.openrouter.model}</span>}
              {selectedRunner === "openrouter" && (
                <span>key {integrationSettings.openrouter.hasApiKey ? "configured" : "missing"}</span>
              )}
              {selectedRunner === "nbrain" && <span>model {integrationSettings.nbrain.model}</span>}
              {selectedRunner === "nbrain" && (
                <span>key {integrationSettings.nbrain.hasApiKey ? "configured" : "missing"}</span>
              )}
            </div>
            <div className="page-form-grid">
              <label className="field">
                Runner
                <select value={selectedRunner} onChange={(e) => setSelectedRunner(e.target.value)}>
                  {runners.map((runner) => (
                    <option key={runner.id} value={runner.id} disabled={!runner.available}>
                      {runner.label} {!runner.available ? "(unavailable)" : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                Output path
                <input value={taskOutputPath} onChange={(e) => setTaskOutputPath(e.target.value)} />
              </label>
              {(selectedRunner === "openrouter" || selectedRunner === "nbrain") && (
                <label className="field">
                  {selectedRunner === "openrouter" ? "OpenRouter model" : "NBrain model"}
                  <input
                    value={selectedRunner === "openrouter" ? integrationSettings.openrouter.model : integrationSettings.nbrain.model}
                    onChange={(e) =>
                      setIntegrationSettings((prev) =>
                        selectedRunner === "openrouter"
                          ? { ...prev, openrouter: { ...prev.openrouter, model: e.target.value } }
                          : { ...prev, nbrain: { ...prev.nbrain, model: e.target.value } },
                      )
                    }
                  />
                </label>
              )}
            </div>
            <label className="field">
              Task prompt
              <textarea className="field-textarea short" value={taskPrompt} onChange={(e) => setTaskPrompt(e.target.value)} />
            </label>
            <div className="controls-row">
              <button className="btn btn-primary" onClick={runTaskWithRunner} disabled={!selectedRunnerInfo?.available || runState === "running"}>
                Run with {selectedRunnerInfo?.label}
              </button>
              <button className="btn" onClick={() => setTaskPrompt(DEFAULT_TASK_PROMPT)}>Reset Prompt</button>
              {(selectedRunner === "openrouter" || selectedRunner === "gemini" || selectedRunner === "nbrain") && (
                <button className="btn" onClick={() => setSelectedPageId("process-settings")}>Edit Provider Settings</button>
              )}
            </div>
          </section>
        );

      case "runner-matrix":
        return (
          <section className="content-block">
            <h3>Runner Matrix</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Runner</th>
                    <th>Kind</th>
                    <th>Available</th>
                    <th>PTY</th>
                    <th>Prompt Required</th>
                  </tr>
                </thead>
                <tbody>
                  {runners.map((runner) => (
                    <tr key={runner.id}>
                      <td>{runner.label}</td>
                      <td>{runner.kind}</td>
                      <td>{runner.available ? "yes" : "no"}</td>
                      <td>{runner.pty ? "yes" : "no"}</td>
                      <td>{runner.requiresPrompt ? "yes" : "no"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );

      case "artifacts":
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
            {!artifacts.length && renderEmptyState("No artifacts yet", "Run a launch or dry run to populate outputs.", "Go to Launch", () => setSelectedPageId("process-launch"))}
          </section>
        );

      case "handoff":
        return (
          <section className="content-block">
            <h3>Delivery Handoff</h3>
            <div className="metric-grid">
              <article className="metric-card">
                <span>Config path</span>
                <strong>{configPath}</strong>
              </article>
              <article className="metric-card">
                <span>Selected references</span>
                <strong>{selectedReferenceIds.length}</strong>
              </article>
              <article className="metric-card">
                <span>Artifacts</span>
                <strong>{artifacts.length}</strong>
              </article>
              <article className="metric-card">
                <span>Last export</span>
                <strong>{exportedAt || "pending"}</strong>
              </article>
              <article className="metric-card">
                <span>Handoff readiness</span>
                <strong>{handoffReadiness}%</strong>
              </article>
            </div>
            <div className="list-grid">
              <article className="list-card">
                <h4>Next action checklist</h4>
                <ul>
                  <li>Confirm final 30 references for FAL queue.</li>
                  <li>Run focused/comprehensive launch based on readiness.</li>
                  <li>Capture final outputs and publish deliverables.</li>
                </ul>
              </article>
              <article className="list-card">
                <h4>Runtime</h4>
                <ul>
                  <li>Bridge: {bridgeOnline ? "online" : "offline"}</li>
                  <li>Run state: {runState}</li>
                  <li>Runner selected: {selectedRunnerInfo?.label ?? "n/a"}</li>
                </ul>
              </article>
            </div>
          </section>
        );

      case "publish-notebooklm":
        return (
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
        );

      case "wiki-handoff":
        return (
          <section className="content-block">
            <h3>Wave 8A · Wiki Docs Handoff</h3>
            <p>Post-pipeline step: run the <strong>wiki-doc-generator</strong> skill against <code>.brandmint/outputs/*.json</code>.</p>
            <div className="list-grid">
              <article className="list-card">
                <h4>Expected output</h4>
                <ul>
                  <li>Structured markdown wiki pages from wave outputs</li>
                  <li>Parallel dispatch across documentation sections</li>
                  <li>Handoff folder for Astro conversion</li>
                </ul>
              </article>
              <article className="list-card">
                <h4>Checklist</h4>
                <ul>
                  <li>Wave outputs present in <code>.brandmint/outputs/</code></li>
                  <li>Reference assets mapped and available</li>
                  <li>Content grouping validated before Astro step</li>
                </ul>
              </article>
            </div>
            <div className="controls-row">
              <button
                className={`btn ${wikiHandoffDone ? "btn-primary" : ""}`}
                onClick={() => {
                  setWikiHandoffDone((prev) => !prev);
                  pushLocalLog("info", `Wiki handoff marked ${!wikiHandoffDone ? "done" : "pending"}.`);
                }}
              >
                {wikiHandoffDone ? "Wiki Handoff Done" : "Mark Wiki Handoff Done"}
              </button>
            </div>
          </section>
        );

      case "astro-build":
        return (
          <section className="content-block">
            <h3>Wave 8B · Astro Build Handoff</h3>
            <p>Post-wiki step: use <strong>markdown-to-astro-wiki</strong> flow to build the glassmorphism Astro docs site.</p>
            <div className="code-preview">
{`# canonical handoff sequence
./scripts/init-astro-wiki.sh my-wiki
./scripts/process-markdown.sh wiki-output/ my-wiki/src/content/docs --images generated/
cd my-wiki && bun run build`}
            </div>
            <div className="controls-row">
              <button
                className={`btn ${astroHandoffDone ? "btn-primary" : ""}`}
                onClick={() => {
                  setAstroHandoffDone((prev) => !prev);
                  pushLocalLog("info", `Astro handoff marked ${!astroHandoffDone ? "done" : "pending"}.`);
                }}
              >
                {astroHandoffDone ? "Astro Handoff Done" : "Mark Astro Handoff Done"}
              </button>
            </div>
          </section>
        );

      default:
        return null;
    }
  }

  return (
    <div className="studio-shell frame-shell">

      <header className="studio-header hud-header">
        <button className="sidebar-toggle-btn" onClick={() => setSidebarCollapsed((prev) => !prev)} title={sidebarCollapsed ? "Show sidebar" : "Hide sidebar"}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {sidebarCollapsed ? (
              <><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></>
            ) : (
              <><rect x="3" y="3" width="7" height="18" rx="1"/><line x1="14" y1="6" x2="21" y2="6"/><line x1="14" y1="12" x2="21" y2="12"/><line x1="14" y1="18" x2="21" y2="18"/></>
            )}
          </svg>
        </button>
        <div className="header-breadcrumb">
          <strong>Brandmint</strong>
          <span style={{ color: "var(--fg-tertiary)" }}>/</span>
          <strong>{selectedPage?.title}</strong>
        </div>
        <div className="hud-cell-right">
          <span className={`status-pill ${bridgeOnline ? "ok" : "warn"}`}>
            <span className={`status-dot ${bridgeOnline ? "pulse" : "danger"}`} />
            {bridgeOnline ? "online" : "offline"}
          </span>
          <span className={`status-pill ${runState === "running" || runState === "retrying" ? "ok" : ""}`}>
            <span className={`status-dot ${runState === "running" || runState === "retrying" ? "pulse" : ""}`} />
            {runState}
          </span>
          <button className="header-icon-btn" onClick={() => setSelectedPageId("process-history")} title="Run History">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </button>
          <button className="header-icon-btn" onClick={() => setSelectedPageId("process-settings")} title="Settings (⌘,)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          </button>
          <button className="btn" onClick={() => setCommandPaletteOpen(true)} title="Command palette (⌘K)">⌘K</button>
        </div>
      </header>

      <div className={`studio-grid ${sidebarCollapsed ? "sidebar-collapsed" : ""}`} style={!sidebarCollapsed ? { gridTemplateColumns: `${sidebarWidth}px 1fr` } as React.CSSProperties : undefined}>
        <aside className="process-sidebar" style={{ position: "relative" }}>
          <div className={`sidebar-resize-handle${isResizingSidebar ? " dragging" : ""}`} onMouseDown={() => setIsResizingSidebar(true)} />
          {/* Quick-access app section */}
          <div className="sidebar-quick-access">
            <button className={`quick-access-btn${selectedPage?.kind === "settings" ? " active" : ""}`} onClick={() => setSelectedPageId("process-settings")}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
              Settings
            </button>
            <button className={`quick-access-btn${selectedPage?.kind === "history" ? " active" : ""}`} onClick={() => setSelectedPageId("process-history")}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              History
            </button>
            <button className={`quick-access-btn${selectedPage?.kind === "output-viewer" ? " active" : ""}`} onClick={() => setSelectedPageId("process-output-viewer")}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              Outputs
            </button>
          </div>

          {recentProjects.length > 0 && (
            <div className="sidebar-recent-projects">
              <small className="sidebar-section-label">Recent Projects</small>
              {recentProjects.slice(0, 3).map((proj) => (
                <button key={proj.path} className="quick-access-btn project-btn" onClick={() => {
                  setConfigPath(proj.path);
                  setProjectName(proj.name);
                  setScenario(proj.scenario);
                  showToast(`Loaded project: ${proj.name}`, "info");
                }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
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
                    <span>{done}/{wave.pages.length} done</span>
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
                        onContextMenu={(e) => { e.preventDefault(); setContextMenu({ x: Math.min(e.clientX, window.innerWidth - 180), y: Math.min(e.clientY, window.innerHeight - 120), pageId: page.id }); }}
                      >
                        <span>{processPages.findIndex((row) => row.id === page.id) + 1}</span>
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

        <main className="process-content">
          <section className="page-hero">
            <p className="page-index">{selectedPage ? waveForPage(selectedPage).label : ""} &middot; Page {selectedPageIndex + 1} of {processPages.length}</p>
            <h2>{selectedPage?.title}</h2>
            <p>{selectedPage?.objective}</p>
            <div className="chip-row" style={{ marginTop: 8 }}>
              {selectedPage?.focus.map((item) => <span key={item}>{item}</span>)}
            </div>
          </section>

          <div key={pageTransitionKey} className="content-main-layout page-transition-enter page-transition-active">
            {!bridgeOnline && !selectedPage?.kind?.startsWith("settings") && !selectedPage?.kind?.startsWith("history") ? (
              <div style={{ padding: 24 }}>
                <div className="skeleton skeleton-block" />
                <div className="skeleton skeleton-line" style={{ width: "80%" }} />
                <div className="skeleton skeleton-line" style={{ width: "55%" }} />
                <div className="skeleton skeleton-line" />
                <div className="skeleton skeleton-block" style={{ marginTop: 16 }} />
              </div>
            ) : selectedPage ? renderProcessPage(selectedPage) : <p>No page selected.</p>}
          </div>
        </main>
      </div>

      <footer className="studio-footer">
        <span>{statusMessage}</span>
        <span>{projectName}</span>
        <span>{scenario}</span>
        <span>{progressSummary.percent}% complete</span>
        {progressSummary.attention > 0 && <span style={{ color: "var(--accent-error)" }}>{progressSummary.attention} attention</span>}
        {updateAvailable && (
          <span className="update-badge" title={`Update available: ${updateAvailable}`}>
            v{updateAvailable}
          </span>
        )}
      </footer>

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

      {/* Toast notifications */}
      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map((t) => (
            <div key={t.id} className={`toast ${t.kind}${t.exiting ? " exiting" : ""}`}>
              <span className="toast-icon">{t.kind === "success" ? "\u2713" : t.kind === "error" ? "\u2717" : "\u2139"}</span>
              <span className="toast-message">{t.message}</span>
              <button className="toast-dismiss" onClick={() => dismissToast(t.id)}>&times;</button>
            </div>
          ))}
        </div>
      )}

      {/* Drag-drop overlay */}
      {isDraggingOver && (
        <div className="drop-overlay">
          <div className="drop-overlay-inner">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>Drop config file to load</p>
            <small>.yaml &middot; .md &middot; .json</small>
          </div>
        </div>
      )}

      {/* Context menu */}
      {contextMenu && (() => {
        const ctxPage = processPages.find((p) => p.id === contextMenu.pageId);
        return (
          <div className="context-menu" style={{ left: contextMenu.x, top: contextMenu.y }}>
            <button className="context-menu-item" onClick={() => { if (ctxPage) setSelectedPageId(ctxPage.id); setContextMenu(null); }}>
              Open <small>Enter</small>
            </button>
            <button className="context-menu-item" onClick={() => { if (ctxPage) navigator.clipboard.writeText(ctxPage.title); setContextMenu(null); showToast("Copied title", "info"); }}>
              Copy title <small>⌘C</small>
            </button>
            <div className="context-menu-divider" />
            <button className="context-menu-item" onClick={() => {
              if (ctxPage) {
                const status = pageStatusMap[ctxPage.id];
                pushLocalLog("info", `Marked "${ctxPage.title}" as ${status === "done" ? "pending" : "done"}`);
                showToast(`${ctxPage.title}: ${status === "done" ? "reset" : "marked done"}`, "success");
              }
              setContextMenu(null);
            }}>
              {pageStatusMap[contextMenu.pageId] === "done" ? "Mark pending" : "Mark done"}
            </button>
          </div>
        );
      })()}
    </div>
  );
}
