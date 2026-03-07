// ── Brandmint shared types ──────────────────────────────────────────

export type RunState = "idle" | "running" | "retrying" | "aborted";

export type Task = {
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

export type Sprint = {
  sprint_id: string;
  duration_weeks: number;
  focus: string;
  tasks: Task[];
};

export type Phase = {
  phase_id: string;
  name: string;
  objective: string;
  sprints: Sprint[];
};

export type TaskmasterPlan = {
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

export type BridgeLog = {
  id: number;
  ts: string;
  level: string;
  message: string;
};

export type ArtifactItem = {
  name: string;
  path: string;
  relativePath: string;
  size: number;
  modifiedAt: string;
  extension: string;
  group: string;
};

export type ReferenceImage = {
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

export type RunnerInfo = {
  id: string;
  label: string;
  kind: string;
  available: boolean;
  supportsOutputPath: boolean;
  requiresPrompt: boolean;
  pty: boolean;
  description: string;
};

export type IntegrationSettings = {
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

export type PhaseSummary = Phase & {
  index: number;
  taskCount: number;
  estimatedHours: number;
  laneCounts: Record<string, number>;
  tasks: Task[];
};

export type ExtractedDraft = {
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

export type ConfigDraft = {
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

export type PageKind =
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

export type ProcessPage = {
  id: string;
  title: string;
  track: string;
  kind: PageKind;
  objective: string;
  focus: string[];
};

export type PageStatus = "pending" | "active" | "done" | "attention";

export type WaveGroup = {
  id: string;
  label: string;
  pages: ProcessPage[];
};

export type CommandAction = {
  id: string;
  label: string;
  hint?: string;
  run: () => void;
};

export type Toast = {
  id: number;
  message: string;
  kind: "success" | "error" | "info";
  exiting?: boolean;
};

export type RunHistoryEntry = {
  id: string;
  scenario: string;
  waves: string;
  startedAt: string;
  duration: number;
  status: "success" | "failed" | "aborted";
  projectName: string;
  configPath: string;
};

export type RecentProject = {
  name: string;
  path: string;
  lastOpened: string;
  scenario: string;
};

export type AppPreferences = {
  fontSize: "default" | "large" | "xlarge";
  sidebarWidth: number;
  autoSave: boolean;
  showNotifications: boolean;
  logRetention: number;
};

// ── Constants ───────────────────────────────────────────────────────

export const DEFAULT_PREFERENCES: AppPreferences = {
  fontSize: "large",
  sidebarWidth: 280,
  autoSave: true,
  showNotifications: true,
  logRetention: 500,
};

export const HISTORY_KEY = "brandmint-run-history";
export const PROJECTS_KEY = "brandmint-recent-projects";
export const PREFS_KEY = "brandmint-preferences";
export const DRAFT_KEY = "brandmint-process-studio-v3";
export const DEFAULT_TASK_PROMPT =
  "Generate a markdown update for this brand run with completed work, risks, and next steps.";

export const DEFAULT_INTEGRATION_SETTINGS: IntegrationSettings = {
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

export const FALLBACK_RUNNERS: RunnerInfo[] = [
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

export const emptyExtraction: ExtractedDraft = {
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
