import { useEffect, useState } from "react";
import { isTauri, listenEvent } from "../lib/tauri";
import { PRODUCT_NAME, PRODUCT_VERSION } from "../lib/appMeta";

type SidecarStatus = "starting" | "ready" | "unhealthy" | "failed";

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

    const unlisteners: (() => void)[] = [];

    listenEvent("sidecar-status", (payload) => {
      const data = payload as { status: string; error?: string };
      if (data.status === "ready") {
        setStatus("ready");
      } else if (data.status === "failed" || data.status === "unhealthy") {
        setStatus(data.status as SidecarStatus);
        setError(data.error || "Unknown error");
      }
    }).then((unlisten) => unlisteners.push(unlisten));

    // Timeout fallback: if sidecar doesn't report ready in 20s,
    // show the app anyway (bridge might already be running externally)
    const timeout = setTimeout(() => {
      setStatus((prev) => (prev === "starting" ? "ready" : prev));
    }, 20000);

    return () => {
      clearTimeout(timeout);
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
        <h1 style={styles.title}>{PRODUCT_NAME}</h1>

        {status === "starting" && (
          <>
            <p style={styles.message}>Starting {PRODUCT_NAME}{dots}</p>
            <div style={styles.progressTrack}>
              <div style={styles.progressFill} />
            </div>
          </>
        )}

        {(status === "failed" || status === "unhealthy") && (
          <>
            <p style={{ ...styles.message, color: "#ff3b3b" }}>{PRODUCT_NAME} bridge failed to start</p>
            <p style={styles.error}>{error}</p>
            <button
              style={styles.retryBtn}
              onClick={() => {
                setStatus("starting");
                setError("");
                // Trigger sidecar restart via invoke
                import("@tauri-apps/api/core").then(({ invoke }) => {
                  invoke("restart_sidecar").catch((e) => {
                    setStatus("failed");
                    setError(String(e));
                  });
                });
              }}
            >
              Retry
            </button>
            <button
              style={{ ...styles.retryBtn, background: "transparent", border: "1px solid rgba(255,255,255,0.2)" }}
              onClick={() => setStatus("ready")}
            >
              Continue anyway
            </button>
          </>
        )}

        <p style={styles.version}>v{PRODUCT_VERSION}</p>
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
