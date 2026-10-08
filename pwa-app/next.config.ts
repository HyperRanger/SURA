import path from "node:path";
import type { NextConfig } from "next";

// `VERCEL_ENV` is available at build time. Force the public environment for a
// production deployment so client-side routing cannot accidentally inherit a
// development value and send bank users to localhost.
const publicAppEnvironment =
  process.env.VERCEL_ENV === "production"
    ? "production"
    : (process.env.NEXT_PUBLIC_APP_ENV ?? "development");

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_APP_ENV: publicAppEnvironment,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
      {
        source: "/sw.js",
        headers: [
          { key: "Content-Type", value: "application/javascript; charset=utf-8" },
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
          { key: "Content-Security-Policy", value: "default-src 'self'; script-src 'self'" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ]
  },
  // this app sits inside the website's folder, which has its own lockfile. pin the
  // root here so turbopack never resolves modules from the website by mistake
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
