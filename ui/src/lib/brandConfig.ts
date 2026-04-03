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

export type ReviewState = "needs_review" | "confirmed" | "edited";

export type SourceSnippet = {
  snippet_id: string;
  text: string;
  start_offset: number;
  end_offset: number;
};

export type ReviewField = {
  label: string;
  sourceKeys: string[];
  confidence: number;
  reviewState: ReviewState;
  sourceSnippets: SourceSnippet[];
  extractedValue: string;
  currentValue: string;
};

export type ReviewSummary = {
  pendingFields: string[];
  editedFields: string[];
  fields: Record<string, ReviewField>;
};

export type ConfigApproval = {
  state: "draft" | "approved" | "superseded";
  approvedBy: string;
  approvedAt: string;
  approvalNote: string;
  fingerprintValue: string;
};

type MetadataLike = {
  document?: { state?: string } | null;
  review?: {
    pending_fields?: string[];
    edited_fields?: string[];
    fields?: Record<string, Record<string, unknown>>;
  } | null;
  approval?: {
    approved_by?: string;
    approved_at?: string;
    approval_note?: string;
    fingerprint_value?: string;
  } | null;
} | null;

function asMetadata(value: unknown): MetadataLike {
  if (!value || typeof value !== "object") return null;
  return value as MetadataLike;
}

type ExtractionKey = keyof Omit<ExtractedDraft, "confidence">;

type TrackedField = {
  extractionKey: ExtractionKey;
  fieldPath: string;
  label: string;
  sourceKeys: string[];
};

const TRACKED_FIELDS: TrackedField[] = [
  { extractionKey: "productName", fieldPath: "brand.name", label: "Brand name", sourceKeys: ["product_name", "name", "heading"] },
  { extractionKey: "category", fieldPath: "brand.domain", label: "Brand domain", sourceKeys: ["category", "domain", "industry"] },
  { extractionKey: "audience", fieldPath: "audience.personaName", label: "Audience", sourceKeys: ["target_audience", "audience", "for_who"] },
  { extractionKey: "problem", fieldPath: "audience.painPoints", label: "Pain points", sourceKeys: ["problem", "pain_points", "challenge"] },
  { extractionKey: "valueProposition", fieldPath: "positioning.statement", label: "Positioning statement", sourceKeys: ["value_proposition", "promise", "solution"] },
  { extractionKey: "differentiators", fieldPath: "positioning.pillars", label: "Identity pillars", sourceKeys: ["differentiators", "features", "benefits"] },
  { extractionKey: "voiceTone", fieldPath: "brand.voice", label: "Brand voice", sourceKeys: ["voice_tone", "voice", "tone"] },
  { extractionKey: "voiceTone", fieldPath: "brand.tone", label: "Brand tone", sourceKeys: ["voice_tone", "voice", "tone"] },
  { extractionKey: "launchGoal", fieldPath: "campaign.primaryObjective", label: "Primary objective", sourceKeys: ["launch_goal", "objective", "cta"] },
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

export function parseProductMd(markdown: string): ExtractedDraft {
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

export function draftToSemanticConfig(
  draft: ConfigDraft,
  existingSemanticConfig?: Record<string, unknown> | null,
): Record<string, unknown> {
  const next = structuredClone(existingSemanticConfig || {});
  next.brand = {
    ...(typeof next.brand === "object" && next.brand ? (next.brand as Record<string, unknown>) : {}),
    name: draft.brand.name,
    domain: draft.brand.domain,
    voice: draft.brand.voice,
    tone: draft.brand.tone,
  };
  next.audience = {
    ...(typeof next.audience === "object" && next.audience ? (next.audience as Record<string, unknown>) : {}),
    persona_name: draft.audience.personaName,
    pain_points: draft.audience.painPoints,
  };
  next.positioning = {
    ...(typeof next.positioning === "object" && next.positioning ? (next.positioning as Record<string, unknown>) : {}),
    statement: draft.positioning.statement,
    identity_pillars: draft.positioning.pillars
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean),
  };
  next.campaign = {
    ...(typeof next.campaign === "object" && next.campaign ? (next.campaign as Record<string, unknown>) : {}),
    primary_objective: draft.campaign.primaryObjective,
  };
  next.visual = {
    ...(typeof next.visual === "object" && next.visual ? (next.visual as Record<string, unknown>) : {}),
    palette_mood: draft.visual.paletteMood,
    typography: draft.visual.typography,
    surface_style: draft.visual.surfaceStyle,
  };
  return next;
}

export function semanticConfigToDraft(semanticConfig?: Record<string, unknown> | null): ConfigDraft {
  const draft = defaultConfigDraft();
  if (!semanticConfig) return draft;
  const brand = (semanticConfig.brand as Record<string, unknown> | undefined) || {};
  const audience = (semanticConfig.audience as Record<string, unknown> | undefined) || {};
  const positioning = (semanticConfig.positioning as Record<string, unknown> | undefined) || {};
  const campaign = (semanticConfig.campaign as Record<string, unknown> | undefined) || {};
  const visual = (semanticConfig.visual as Record<string, unknown> | undefined) || {};

  draft.brand.name = String(brand.name || draft.brand.name);
  draft.brand.domain = String(brand.domain || draft.brand.domain);
  draft.brand.voice = String(brand.voice || draft.brand.voice);
  draft.brand.tone = String(brand.tone || draft.brand.tone);
  draft.audience.personaName = String(audience.persona_name || audience.personaName || draft.audience.personaName);
  draft.audience.painPoints = String(audience.pain_points || audience.painPoints || draft.audience.painPoints);
  draft.positioning.statement = String(positioning.statement || draft.positioning.statement);
  const pillars = Array.isArray(positioning.identity_pillars)
    ? positioning.identity_pillars
    : Array.isArray(positioning.pillars)
      ? positioning.pillars
      : [];
  draft.positioning.pillars = pillars.map((item) => String(item)).join("\n") || draft.positioning.pillars;
  draft.campaign.primaryObjective = String(campaign.primary_objective || campaign.primaryObjective || draft.campaign.primaryObjective);
  draft.visual.paletteMood = String(visual.palette_mood || visual.paletteMood || draft.visual.paletteMood);
  draft.visual.typography = String(visual.typography || draft.visual.typography);
  draft.visual.surfaceStyle = String(visual.surface_style || visual.surfaceStyle || draft.visual.surfaceStyle);
  return draft;
}

function getCurrentValue(draft: ConfigDraft, fieldPath: string): string {
  switch (fieldPath) {
    case "brand.name":
      return draft.brand.name;
    case "brand.domain":
      return draft.brand.domain;
    case "audience.personaName":
      return draft.audience.personaName;
    case "audience.painPoints":
      return draft.audience.painPoints;
    case "positioning.statement":
      return draft.positioning.statement;
    case "positioning.pillars":
      return draft.positioning.pillars;
    case "brand.voice":
      return draft.brand.voice;
    case "brand.tone":
      return draft.brand.tone;
    case "campaign.primaryObjective":
      return draft.campaign.primaryObjective;
    default:
      return "";
  }
}

function buildSnippet(sourceText: string, extractedValue: string, sourceKeys: string[]): SourceSnippet[] {
  const text = sourceText || "";
  const lower = text.toLowerCase();
  const extracted = extractedValue.trim();

  if (extracted) {
    const idx = lower.indexOf(extracted.toLowerCase());
    if (idx >= 0) {
      const start = Math.max(0, idx - 60);
      const end = Math.min(text.length, idx + extracted.length + 60);
      return [{
        snippet_id: `snippet-${idx}`,
        text: text.slice(start, end).trim(),
        start_offset: start,
        end_offset: end,
      }];
    }
  }

  const lines = text.split(/\r?\n/);
  let offset = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    const matched = sourceKeys.some((key) => trimmed.toLowerCase().includes(key.replace(/_/g, " ")));
    if (matched && trimmed) {
      return [{
        snippet_id: `snippet-${offset}`,
        text: trimmed,
        start_offset: offset,
        end_offset: offset + line.length,
      }];
    }
    offset += line.length + 1;
  }

  return [];
}

function fieldConfidence(extractedValue: string, snippets: SourceSnippet[], fieldPath: string): number {
  if (!extractedValue.trim()) return 0.18;
  if (snippets.length > 0) return 0.92;
  if (fieldPath === "positioning.statement") return 0.62;
  if (fieldPath === "positioning.pillars") return 0.74;
  return 0.78;
}

export function buildReviewSummary(
  extraction: ExtractedDraft,
  draft: ConfigDraft,
  productMdText: string,
): ReviewSummary {
  const fields: Record<string, ReviewField> = {};

  for (const row of TRACKED_FIELDS) {
    const extractedValue = String(extraction[row.extractionKey] || "");
    const currentValue = getCurrentValue(draft, row.fieldPath);
    const sourceSnippets = buildSnippet(productMdText, extractedValue, row.sourceKeys);
    const confidence = Number(fieldConfidence(extractedValue, sourceSnippets, row.fieldPath).toFixed(2));
    let reviewState: ReviewState = confidence >= 0.75 ? "confirmed" : "needs_review";
    if (!currentValue.trim()) {
      reviewState = "needs_review";
    } else if (currentValue.trim() !== extractedValue.trim()) {
      reviewState = "edited";
    }

    fields[row.fieldPath] = {
      label: row.label,
      sourceKeys: row.sourceKeys,
      confidence,
      reviewState,
      sourceSnippets,
      extractedValue,
      currentValue,
    };
  }

  const pendingFields = Object.entries(fields)
    .filter(([, value]) => value.reviewState === "needs_review")
    .map(([path]) => path);
  const editedFields = Object.entries(fields)
    .filter(([, value]) => value.reviewState === "edited")
    .map(([path]) => path);

  return {
    pendingFields,
    editedFields,
    fields,
  };
}

export function reviewSummaryFromMetadata(metadataInput: unknown, fallback: ReviewSummary): ReviewSummary {
  const metadata = asMetadata(metadataInput);
  const fields = metadata?.review?.fields;
  if (!fields || typeof fields !== "object") return fallback;

  const nextFields = Object.fromEntries(
    Object.entries(fields).map(([path, value]) => {
      const raw = value || {};
      return [path, {
        label: String(raw.label || path),
        sourceKeys: Array.isArray(raw.source_keys) ? raw.source_keys.map((item) => String(item)) : [],
        confidence: Number(raw.confidence || 0),
        reviewState: String(raw.review_state || "needs_review") as ReviewState,
        sourceSnippets: Array.isArray(raw.source_snippets)
          ? raw.source_snippets.map((snippet, index) => {
              const row = (snippet as Record<string, unknown>) || {};
              return {
                snippet_id: String(row.snippet_id || `snippet-${index}`),
                text: String(row.text || ""),
                start_offset: Number(row.start_offset || 0),
                end_offset: Number(row.end_offset || 0),
              };
            })
          : [],
        extractedValue: String(raw.extracted_value || ""),
        currentValue: String(raw.current_value || ""),
      } satisfies ReviewField];
    }),
  ) as Record<string, ReviewField>;

  return {
    pendingFields: metadata?.review?.pending_fields || fallback.pendingFields,
    editedFields: metadata?.review?.edited_fields || fallback.editedFields,
    fields: nextFields,
  };
}

export function approvalFromMetadata(metadataInput: unknown): ConfigApproval {
  const metadata = asMetadata(metadataInput);
  return {
    state: metadata?.document?.state === "approved" ? "approved" : metadata?.document?.state === "superseded" ? "superseded" : "draft",
    approvedBy: String(metadata?.approval?.approved_by || ""),
    approvedAt: String(metadata?.approval?.approved_at || ""),
    approvalNote: String(metadata?.approval?.approval_note || ""),
    fingerprintValue: String(metadata?.approval?.fingerprint_value || ""),
  };
}
