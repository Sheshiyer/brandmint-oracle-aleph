import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import type { IncomingMessage, ServerResponse } from "http";
import http from "http";

/**
 * Custom /api proxy that silently returns 503 when the Python sidecar
 * isn't reachable, instead of Vite's default ECONNREFUSED error spam.
 */
function sidecarProxy(): Plugin {
  return {
    name: "sidecar-proxy",
    configureServer(server) {
      server.middlewares.use(
        (req: IncomingMessage, res: ServerResponse, next: () => void) => {
          if (!req.url?.startsWith("/api")) {
            return next();
          }

          const proxyReq = http.request(
            {
              hostname: "127.0.0.1",
              port: 4191,
              path: req.url,
              method: req.method,
              headers: { ...req.headers, host: "127.0.0.1:4191" },
            },
            (proxyRes) => {
              res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
              proxyRes.pipe(res);
            }
          );

          proxyReq.on("error", () => {
            if (!res.headersSent) {
              res.writeHead(503, { "Content-Type": "application/json" });
              res.end(
                JSON.stringify({ error: "sidecar starting", ready: false })
              );
            }
          });

          req.pipe(proxyReq);
        }
      );
    },
  };
}

export default defineConfig({
  plugins: [react(), sidecarProxy()],
  server: {
    host: "127.0.0.1",
    port: 4188,
    strictPort: true,
  },
  preview: {
    host: "127.0.0.1",
    port: 4188,
    strictPort: true,
  },
});
