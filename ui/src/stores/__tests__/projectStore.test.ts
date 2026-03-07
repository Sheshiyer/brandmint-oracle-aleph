import { describe, it, expect, beforeEach } from "vitest";
import { useProjectStore } from "../projectStore";

describe("projectStore", () => {
  beforeEach(() => {
    useProjectStore.setState(useProjectStore.getInitialState());
  });

  it("starts with default project name", () => {
    expect(useProjectStore.getState().projectName).toBe("brandmint");
  });

  it("sets project name", () => {
    useProjectStore.getState().setProjectName("new-brand");
    expect(useProjectStore.getState().projectName).toBe("new-brand");
  });

  it("sets scenario", () => {
    useProjectStore.getState().setScenario("comprehensive");
    expect(useProjectStore.getState().scenario).toBe("comprehensive");
  });

  it("advances wizard step", () => {
    useProjectStore.getState().setWizardStep(3);
    expect(useProjectStore.getState().wizardStep).toBe(3);
  });

  it("adds recent project and deduplicates by path", () => {
    const proj = { name: "test", path: "/a", lastOpened: "2025-01-01", scenario: "focused" };
    useProjectStore.getState().addRecentProject(proj);
    useProjectStore.getState().addRecentProject(proj);
    // Same path should be deduplicated
    expect(useProjectStore.getState().recentProjects).toHaveLength(1);
  });

  it("clears draft resets to defaults", () => {
    useProjectStore.getState().setProjectName("changed");
    useProjectStore.getState().setWizardStep(5);
    useProjectStore.getState().clearDraft();
    expect(useProjectStore.getState().projectName).toBe("brandmint");
    expect(useProjectStore.getState().wizardStep).toBe(0);
  });
});
