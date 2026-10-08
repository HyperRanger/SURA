import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // sign in on this site is for partner banks only. the old member and demo
  // entry points, and any links to them, land on the bank console sign in
  async redirects() {
    return ["/login", "/signup", "/verify", "/demo"].map((source) => ({
      source,
      destination: "/bank/login",
      permanent: false,
    }));
  },
};

export default nextConfig;
