import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

let APP_VERSION;
try {
  APP_VERSION = readFileSync(join(__dirname, "../VERSION"), "utf-8").trim();
} catch {
  APP_VERSION = "1.5.1";
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    typedRoutes: true,
  },
  env: {
    APP_VERSION,
  },
};

export default nextConfig;
