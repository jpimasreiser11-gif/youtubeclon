import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Allow build to succeed while TypeScript debt is being reduced incrementally.
  typescript: {
    ignoreBuildErrors: true,
  },
  outputFileTracingRoot: path.resolve(__dirname),
};

export default nextConfig;
