import { useState } from "react";
import { useSettingsStore } from "../stores/settingsStore";
import { useProjectStore } from "../stores/projectStore";
import { usePipelineStore } from "../stores/pipelineStore";
import { useUiStore } from "../stores/uiStore";
import { DEFAULT_INTEGRATION_SETTINGS } from "../types";

export default function SettingsPage() {
  const integrationSettings = useSettingsStore((s) => s.integrationSettings);
  const setIntegrationSettings = useSettingsStore((s) => s.setIntegrationSettings);
  const updateIntegrationSettings = useSettingsStore((s) => s.updateIntegrationSettings);
  const preferences = useSettingsStore((s) => s.preferences);
  const updatePreferences = useSettingsStore((s) => s.updatePreferences);
  const runners = useSettingsStore((s) => s.runners);
  const setRunners = useSettingsStore((s) => s.setRunners);

  const recentProjects = useProjectStore((s) => s.recentProjects);
  const setBrandFolder = useProjectStore((s) => s.setBrandFolder);
  const setProjectName = useProjectStore((s) => s.setProjectName);
  const setScenario = useProjectStore((s) => s.setScenario);

  const pushLocalLog = usePipelineStore((s) => s.pushLocalLog);
  const addToast = useUiStore((s) => s.addToast);

  const [openrouterApiKeyInput, setOpenrouterApiKeyInput] = useState("");
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [updateAvailable] = useState<string | null>(null);

  async function saveIntegrationSettings(options?: { clearOpenrouter?: boolean }) {
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
      if (openrouterApiKeyInput.trim()) payload.openrouterApiKey = openrouterApiKeyInput.trim();
      if (options?.clearOpenrouter) payload.clearOpenrouterApiKey = true;

      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to save settings");
      const data = await res.json();
      const next = data.settings;
      if (next) {
        setIntegrationSettings({
          openrouter: { ...DEFAULT_INTEGRATION_SETTINGS.openrouter, ...(next.openrouter || {}) },
          nbrain: { ...DEFAULT_INTEGRATION_SETTINGS.nbrain, ...(next.nbrain || {}) },
          defaults: { ...DEFAULT_INTEGRATION_SETTINGS.defaults, ...(next.defaults || {}) },
        });
      }
      setOpenrouterApiKeyInput("");
    } catch (error) {
      pushLocalLog("error", `Settings save failed: ${(error as Error).message}`);
    } finally {
      setSettingsSaving(false);
    }
  }

  async function loadIntegrationSettings() {
    try {
      const res = await fetch("/api/settings");
      if (!res.ok) return;
      const data = await res.json();
      const next = data.settings;
      if (next) {
        setIntegrationSettings({
          openrouter: { ...DEFAULT_INTEGRATION_SETTINGS.openrouter, ...(next.openrouter || {}) },
          nbrain: { ...DEFAULT_INTEGRATION_SETTINGS.nbrain, ...(next.nbrain || {}) },
          defaults: { ...DEFAULT_INTEGRATION_SETTINGS.defaults, ...(next.defaults || {}) },
        });
      }
    } catch {
      pushLocalLog("warn", "Unable to load provider settings.");
    }
  }

  return (
    <>
      <div className="settings-section">
        <h4>Appearance</h4>
        <div className="settings-row">
          <div>
            <div className="settings-row-label">Notifications</div>
            <div className="settings-row-desc">Show native OS notifications for run events</div>
          </div>
          <div className="settings-row-control">
            <select value={preferences.showNotifications ? "on" : "off"} onChange={(e) => updatePreferences({ showNotifications: e.target.value === "on" })}>
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
            <select value={preferences.autoSave ? "on" : "off"} onChange={(e) => updatePreferences({ autoSave: e.target.value === "on" })}>
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
            <select value={preferences.logRetention} onChange={(e) => updatePreferences({ logRetention: Number(e.target.value) })}>
              <option value="200">200</option>
              <option value="500">500</option>
              <option value="1000">1000</option>
            </select>
          </div>
        </div>
      </div>

      {recentProjects.length > 0 && (
        <div className="settings-section">
          <h4>Recent Projects</h4>
          <div className="project-grid">
            {recentProjects.map((proj) => (
              <div key={proj.path} className="project-card" onClick={() => {
                setBrandFolder(proj.path);
                setProjectName(proj.name);
                setScenario(proj.scenario);
                addToast(`Loaded project: ${proj.name}`, "info");
              }}>
                <h4>{proj.name}</h4>
                <p>{proj.path}</p>
                <p style={{ marginTop: 4 }}>{proj.scenario} &middot; {new Date(proj.lastOpened).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

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
            <input value={integrationSettings.openrouter.model} onChange={(e) => updateIntegrationSettings((prev) => ({ ...prev, openrouter: { ...prev.openrouter, model: e.target.value } }))} />
          </label>
          <label className="field">
            Model router mode
            <select value={integrationSettings.openrouter.routeMode} onChange={(e) => updateIntegrationSettings((prev) => ({ ...prev, openrouter: { ...prev.openrouter, routeMode: e.target.value } }))}>
              <option value="balanced">balanced</option>
              <option value="quality">quality</option>
              <option value="speed">speed</option>
            </select>
          </label>
          <label className="field">
            Preferred runner
            <select value={integrationSettings.defaults.preferredRunner} onChange={(e) => updateIntegrationSettings((prev) => ({ ...prev, defaults: { ...prev.defaults, preferredRunner: e.target.value } }))}>
              {runners.map((runner) => (<option key={runner.id} value={runner.id}>{runner.label}</option>))}
            </select>
          </label>
        </div>
        <div className="controls-row">
          <button className="btn btn-primary" onClick={() => { void saveIntegrationSettings(); addToast("Settings saved", "success"); }} disabled={settingsSaving}>{settingsSaving ? "Saving..." : "Save Settings"}</button>
          <button className="btn" onClick={() => void loadIntegrationSettings()}>Reload</button>
          <button className="btn btn-danger" onClick={() => void saveIntegrationSettings({ clearOpenrouter: true })}>Clear OpenRouter Key</button>
        </div>
      </div>

      <div className="settings-section">
        <h4>About</h4>
        <div className="settings-row">
          <div>
            <div className="settings-row-label">Version</div>
            <div className="settings-row-desc">Brandmint Desktop v4.3.1</div>
          </div>
          {updateAvailable && <span className="update-badge">v{updateAvailable} available</span>}
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
}
