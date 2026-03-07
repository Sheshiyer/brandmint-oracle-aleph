import { describe, it, expect, beforeEach } from "vitest";
import { useUiStore } from "../uiStore";

describe("uiStore", () => {
  beforeEach(() => {
    useUiStore.setState(useUiStore.getInitialState());
  });

  it("starts with journey as active page", () => {
    expect(useUiStore.getState().activePage).toBe("journey");
  });

  it("sets active page", () => {
    useUiStore.getState().setActivePage("settings");
    expect(useUiStore.getState().activePage).toBe("settings");
  });

  it("toggles sidebar collapsed", () => {
    expect(useUiStore.getState().sidebarCollapsed).toBe(false);
    useUiStore.getState().toggleSidebar();
    expect(useUiStore.getState().sidebarCollapsed).toBe(true);
  });

  it("bumps page transition key", () => {
    const initial = useUiStore.getState().pageTransitionKey;
    useUiStore.getState().bumpPageTransition();
    expect(useUiStore.getState().pageTransitionKey).toBe(initial + 1);
  });

  it("manages command palette state", () => {
    useUiStore.getState().setCommandPaletteOpen(true);
    expect(useUiStore.getState().commandPaletteOpen).toBe(true);
    useUiStore.getState().setCommandQuery("run");
    expect(useUiStore.getState().commandQuery).toBe("run");
  });

  it("removes toast by id", () => {
    // Manually inject a toast to avoid setTimeout side effects
    useUiStore.setState({
      toasts: [{ id: 42, message: "hello", kind: "info" }],
    });
    useUiStore.getState().removeToast(42);
    expect(useUiStore.getState().toasts).toHaveLength(0);
  });
});
