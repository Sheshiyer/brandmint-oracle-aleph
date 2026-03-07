import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStore } from "../pipelineStore";

describe("pipelineStore", () => {
  beforeEach(() => {
    usePipelineStore.setState(usePipelineStore.getInitialState());
  });

  it("starts with idle run state", () => {
    expect(usePipelineStore.getState().runState).toBe("idle");
  });

  it("starts with bridge offline", () => {
    expect(usePipelineStore.getState().bridgeOnline).toBe(false);
  });

  it("updates run state", () => {
    usePipelineStore.getState().setRunState("running");
    expect(usePipelineStore.getState().runState).toBe("running");
  });

  it("sets bridge online status", () => {
    usePipelineStore.getState().setBridgeOnline(true);
    expect(usePipelineStore.getState().bridgeOnline).toBe(true);
  });

  it("pushes local log entries", () => {
    usePipelineStore.getState().pushLocalLog("info", "test message");
    const logs = usePipelineStore.getState().bridgeLogs;
    expect(logs).toHaveLength(1);
    expect(logs[0].level).toBe("info");
    expect(logs[0].message).toBe("test message");
  });

  it("toggles dry run mode", () => {
    expect(usePipelineStore.getState().dryRunMode).toBe(false);
    usePipelineStore.getState().toggleDryRunMode();
    expect(usePipelineStore.getState().dryRunMode).toBe(true);
    usePipelineStore.getState().toggleDryRunMode();
    expect(usePipelineStore.getState().dryRunMode).toBe(false);
  });

  it("adds and clears run history", () => {
    const entry = {
      id: "run-1",
      scenario: "focused",
      waves: "1-7",
      startedAt: new Date().toISOString(),
      duration: 120,
      status: "success" as const,
      projectName: "test",
      configPath: "./config.yaml",
    };
    usePipelineStore.getState().addRunToHistory(entry);
    expect(usePipelineStore.getState().runHistory).toHaveLength(1);
    usePipelineStore.getState().clearRunHistory();
    expect(usePipelineStore.getState().runHistory).toHaveLength(0);
  });

  it("sets active runner id", () => {
    usePipelineStore.getState().setActiveRunnerId("custom-runner");
    expect(usePipelineStore.getState().activeRunnerId).toBe("custom-runner");
  });
});
