import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // this app sits inside the website's folder, which has its own lockfile. pin the
  // root here so turbopack never resolves modules from the website by mistake
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
