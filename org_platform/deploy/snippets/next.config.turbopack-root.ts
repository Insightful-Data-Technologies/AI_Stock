import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

/** Static deploy: `next build` → `out/` for CDN / storage hosting. */
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  // Prevent Turbopack from picking a parent lockfile (e.g. D:\AI_Capital\package-lock.json)
  // and failing to resolve next/package.json from src/app.
  turbopack: {
    root: projectRoot,
  },
};

export default nextConfig;
