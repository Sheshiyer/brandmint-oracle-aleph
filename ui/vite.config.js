var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import http from "http";
/**
 * Custom /api proxy that silently returns 503 when the Python sidecar
 * isn't reachable, instead of Vite's default ECONNREFUSED error spam.
 */
function sidecarProxy() {
    return {
        name: "sidecar-proxy",
        configureServer: function (server) {
            server.middlewares.use(function (req, res, next) {
                var _a;
                if (!((_a = req.url) === null || _a === void 0 ? void 0 : _a.startsWith("/api"))) {
                    return next();
                }
                var proxyReq = http.request({
                    hostname: "127.0.0.1",
                    port: 4191,
                    path: req.url,
                    method: req.method,
                    headers: __assign(__assign({}, req.headers), { host: "127.0.0.1:4191" }),
                }, function (proxyRes) {
                    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
                    proxyRes.pipe(res);
                });
                proxyReq.on("error", function () {
                    if (!res.headersSent) {
                        res.writeHead(503, { "Content-Type": "application/json" });
                        res.end(JSON.stringify({ error: "sidecar starting", ready: false }));
                    }
                });
                req.pipe(proxyReq);
            });
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
