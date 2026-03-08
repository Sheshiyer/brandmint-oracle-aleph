import { useEffect, useState } from "react";
import { apiBridge, isTauri, listenEvent } from "../lib/tauri";

type SidecarStatus = "starting" | "ready" | "unhealthy" | "failed" | "stopped";

const STARTUP_TIMEOUT_MS = 20_000;
const HEALTH_POLL_INTERVAL_MS = 500;

export default function SplashScreen({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<SidecarStatus>("starting");
  const [error, setError] = useState("");
  const [dots, setDots] = useState("");

  useEffect(() => {
    if (!isTauri()) {
      // In browser mode, skip splash — go straight to the app
      setStatus("ready");
      return;
    }

    let cancelled = false;
    const unlisteners: (() => void)[] = [];
    const startupDeadline = Date.now() + STARTUP_TIMEOUT_MS;

    const markFailed = (nextStatus: SidecarStatus, message: string) => {
      if (cancelled) return;
      setStatus(nextStatus);
      setError(message);
    };

    listenEvent("sidecar-status", (payload) => {
      const data = payload as { status: string; error?: string };
      if (data.status === "ready") {
        setStatus("ready");
        setError("");
      } else if (data.status === "failed" || data.status === "unhealthy") {
        markFailed(data.status as SidecarStatus, data.error || "Unknown error");
      } else if (data.status === "stopped" || data.status === "terminated") {
        markFailed("stopped", data.error || "Bridge process stopped");
      }
    }).then((unlisten) => unlisteners.push(unlisten));

    const pollHealth = async () => {
      while (!cancelled) {
        try {
          await apiBridge("get_health");
          if (!cancelled) {
            setStatus("ready");
            setError("");
          }
          return;
        } catch (probeError) {
          if (Date.now() >= startupDeadline) {
            markFailed(
              "failed",
              `Bridge did not become healthy within ${STARTUP_TIMEOUT_MS / 1000}s: ${String(probeError)}`,
            );
            return;
          }
          await new Promise((resolve) => setTimeout(resolve, HEALTH_POLL_INTERVAL_MS));
        }
      }
    };

    void pollHealth();

    return () => {
      cancelled = true;
      unlisteners.forEach((fn) => fn());
    };
  }, []);

  // Animate dots
  useEffect(() => {
    if (status !== "starting") return;
    const timer = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 400);
    return () => clearInterval(timer);
  }, [status]);

  if (status === "ready") {
    return <>{children}</>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>BM</div>
        <h1 style={styles.title}>Brandmint</h1>

        {status === "starting" && (
          <>
            <p style={styles.message}>Starting bridge{dots}</p>
            <div style={styles.progressTrack}>
              <div style={styles.progressFill} />
            </div>
          </>
        )}

        {(status === "failed" || status === "unhealthy") && (
          <>
            <p style={{ ...styles.message, color: "#ff3b3b" }}>Bridge failed to start</p>
            <p style={styles.error}>{error}</p>
            <button
              style={styles.retryBtn}
              onClick={() => {
                setStatus("starting");
                setError("");
                // Trigger sidecar restart via invoke
                import("@tauri-apps/api/core").then(({ invoke }) => {
                  invoke("restart_sidecar")
                    .then(() => {
                      setStatus("ready");
                      setError("");
                    })
                    .catch((e) => {
                      setStatus("failed");
                      setError(String(e));
                    });
                });
              }}
            >
              Retry
            </button>
          </>
        )}

        <p style={styles.version}>v4.3.1</p>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: "fixed",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#050505",
    zIndex: 9999,
  },
  card: {
    textAlign: "center",
    maxWidth: 360,
    padding: 40,
  },
  logo: {
    width: 64,
    height: 64,
    margin: "0 auto 16px",
    borderRadius: 16,
    background: "linear-gradient(135deg, #00ff41, #0af)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 24,
    fontWeight: 800,
    color: "#050505",
    letterSpacing: -1,
  },
  title: {
    margin: "0 0 24px",
    fontSize: 28,
    fontWeight: 600,
    color: "#fff",
    letterSpacing: -0.5,
  },
  message: {
    margin: "0 0 16px",
    fontSize: 14,
    color: "#8a8a8a",
    fontFamily: "'JetBrains Mono', monospace",
  },
  progressTrack: {
    height: 2,
    background: "rgba(255,255,255,0.1)",
    borderRadius: 1,
    overflow: "hidden",
    marginBottom: 24,
  },
  progressFill: {
    height: "100%",
    width: "40%",
    background: "linear-gradient(90deg, #00ff41, #0af)",
    borderRadius: 1,
    animation: "splash-progress 1.5s ease-in-out infinite",
  },
  error: {
    margin: "0 0 16px",
    fontSize: 12,
    color: "#ff3b3b",
    fontFamily: "'JetBrains Mono', monospace",
    wordBreak: "break-all",
  },
  retryBtn: {
    padding: "8px 20px",
    fontSize: 13,
    fontWeight: 500,
    color: "#fff",
    background: "#00ff41",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    marginRight: 8,
    marginBottom: 8,
  },
  version: {
    margin: "24px 0 0",
    fontSize: 11,
    color: "#4b4b4b",
    fontFamily: "'JetBrains Mono', monospace",
  },
};
