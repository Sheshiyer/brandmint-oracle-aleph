import { ChangeEvent } from "react";
import { useProjectStore } from "../stores/projectStore";
import { usePipelineStore } from "../stores/pipelineStore";
import { useUiStore } from "../stores/uiStore";
import { parseProductMd, extractionToConfig, defaultConfigDraft } from "../lib/utils";
import { emptyExtraction } from "../types";
import { pickMarkdownFile, pickFolder, readTextFile } from "../lib/native";
import { isTauri } from "../lib/tauri";

export default function IntakePage() {
  const brandFolder = useProjectStore((s) => s.brandFolder);
  const setBrandFolder = useProjectStore((s) => s.setBrandFolder);
  const productMdPath = useProjectStore((s) => s.productMdPath);
  const setProductMdPath = useProjectStore((s) => s.setProductMdPath);
  const productMdText = useProjectStore((s) => s.productMdText);
  const setProductMdText = useProjectStore((s) => s.setProductMdText);
  const setExtraction = useProjectStore((s) => s.setExtraction);
  const setExtractionConfirmed = useProjectStore((s) => s.setExtractionConfirmed);
  const setWizardStep = useProjectStore((s) => s.setWizardStep);
  const setConfigDraft = useProjectStore((s) => s.setConfigDraft);
  const setConfigPath = useProjectStore((s) => s.setConfigPath);
  const setExportedAt = useProjectStore((s) => s.setExportedAt);
  const setSelectedReferenceIds = (ids: string[]) => {
    // Access reference store directly
    const { useReferenceStore } = require("../stores/referenceStore");
    useReferenceStore.getState().setSelectedReferenceIds(ids);
  };
  const setWikiHandoffDone = useProjectStore((s) => s.setWikiHandoffDone);
  const setAstroHandoffDone = useProjectStore((s) => s.setAstroHandoffDone);

  const pushLocalLog = usePipelineStore((s) => s.pushLocalLog);
  const setStatusMessage = usePipelineStore((s) => s.setStatusMessage);
  const setDryRunMode = usePipelineStore((s) => s.setDryRunMode);
  const setRunState = usePipelineStore((s) => s.setRunState);

  const setSelectedPageId = useUiStore((s) => s.setSelectedPageId);
  const addToast = useUiStore((s) => s.addToast);

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
    useProjectStore.getState().clearDraft();
    setStatusMessage("Draft cleared.");
  }

  async function loadFromBrandFolder() {
    if (!brandFolder.trim()) {
      setStatusMessage("Enter a brand folder first.");
      return;
    }
    try {
      const res = await fetch("/api/intake/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brandFolder: brandFolder.trim(), productMdFile: "product.md", configFile: "brand-config.yaml" }),
      });
      if (!res.ok) throw new Error("Request failed");
      const result = await res.json();
      if (result?.brandFolder) setBrandFolder(String(result.brandFolder));
      if (result?.productMdPath) setProductMdPath(String(result.productMdPath));
      if (typeof result?.productMdText === "string" && result.productMdText.trim()) setProductMdText(result.productMdText);
      if (result?.configPath) setConfigPath(String(result.configPath));
      setStatusMessage("Loaded intake context from brand folder.");
    } catch (error) {
      pushLocalLog("error", `Brand folder load failed: ${(error as Error).message}`);
    }
  }

  async function openFolderDialog(_title: string) {
    return pickFolder();
  }

  async function openFileDialog(_title: string, _filters: { name: string; extensions: string[] }[]) {
    return pickMarkdownFile();
  }

  /** Browse for a product.md, read its contents via native FS, and load into store. */
  async function browseAndReadProductMd() {
    const filePath = await pickMarkdownFile();
    if (!filePath) return;
    setProductMdPath(filePath);
    if (isTauri()) {
      try {
        const text = await readTextFile(filePath);
        setProductMdText(text);
        setStatusMessage(`Loaded ${filePath.split("/").pop() ?? filePath}`);
        addToast(`Product doc loaded: ${filePath.split("/").pop()}`, "success");
      } catch (err) {
        pushLocalLog("error", `Failed to read file: ${(err as Error).message}`);
      }
    } else {
      addToast(`Product doc path: ${filePath}`, "info");
    }
  }

  return (
    <section className="content-block priority-block">
      <h3>Product MD Intake</h3>
      <p>Start here. If Product MD is not provided, set the brand folder and load `product.md` from it.</p>
      <label className="field">
        Brand folder
        <div style={{ display: "flex", gap: 8 }}>
          <input style={{ flex: 1 }} value={brandFolder} onChange={(e) => setBrandFolder(e.target.value)} placeholder="./my-brand" />
          <button className="btn" onClick={async () => { const f = await openFolderDialog("Select brand folder"); if (f) { setBrandFolder(f); addToast(`Brand folder: ${f}`, "success"); } }}>Browse</button>
        </div>
      </label>
      <div className="controls-row">
        <input type="file" accept=".md,.txt" onChange={handleFileUpload} />
        <button className="btn" onClick={() => void loadFromBrandFolder()}>Load From Brand Folder</button>
        <button className="btn" onClick={() => void browseAndReadProductMd()}>Open File</button>
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
}
