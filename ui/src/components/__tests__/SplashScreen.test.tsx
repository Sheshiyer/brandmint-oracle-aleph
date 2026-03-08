import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SplashScreen from "../SplashScreen";
import * as tauriBridge from "../../lib/tauri";

vi.mock("../../lib/tauri", () => ({
  apiBridge: vi.fn(),
  isTauri: vi.fn(),
  listenEvent: vi.fn(),
}));

describe("SplashScreen", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(tauriBridge.isTauri).mockReturnValue(true);
    vi.mocked(tauriBridge.listenEvent).mockResolvedValue(() => {});
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it("reveals the app when the bridge health probe succeeds", async () => {
    vi.useRealTimers();
    vi.mocked(tauriBridge.apiBridge).mockResolvedValue({ ok: true });

    render(
      <SplashScreen>
        <div>App Ready</div>
      </SplashScreen>,
    );

    await waitFor(() => expect(screen.getByText("App Ready")).toBeInTheDocument());
  });

  it("does not continue into the app when the bridge never becomes healthy", async () => {
    vi.mocked(tauriBridge.apiBridge).mockRejectedValue(new Error("bridge down"));

    render(
      <SplashScreen>
        <div>App Ready</div>
      </SplashScreen>,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(20_500);
    });

    expect(screen.getByText("Bridge failed to start")).toBeInTheDocument();
    expect(screen.queryByText("App Ready")).not.toBeInTheDocument();
    expect(screen.queryByText("Continue anyway")).not.toBeInTheDocument();
  });
});
