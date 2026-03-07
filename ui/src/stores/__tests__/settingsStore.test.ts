import { describe, it, expect, beforeEach } from "vitest";
import { useSettingsStore } from "../settingsStore";

describe("settingsStore", () => {
  beforeEach(() => {
    useSettingsStore.setState(useSettingsStore.getInitialState());
  });

  it("starts with default publish stage", () => {
    expect(useSettingsStore.getState().publishStage).toBe("notebooklm");
  });

  it("sets selected runner", () => {
    useSettingsStore.getState().setSelectedRunner("custom");
    expect(useSettingsStore.getState().selectedRunner).toBe("custom");
  });

  it("updates preferences partially", () => {
    useSettingsStore.getState().updatePreferences({ autoSave: false });
    const prefs = useSettingsStore.getState().preferences;
    expect(prefs.autoSave).toBe(false);
    // Other preferences should be unchanged
    expect(prefs.fontSize).toBe("large");
  });

  it("resets settings to defaults", () => {
    useSettingsStore.getState().setSelectedRunner("changed");
    useSettingsStore.getState().setPublishStage("changed");
    useSettingsStore.getState().resetSettings();
    expect(useSettingsStore.getState().selectedRunner).toBe("bm");
    expect(useSettingsStore.getState().publishStage).toBe("notebooklm");
  });
});
