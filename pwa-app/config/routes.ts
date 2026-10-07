import { env } from "@/config/env"

// one place for every path, so a renamed route is a one-line change
export const routes = {
  home: "/",
  signup: "/signup",
  login: "/login",
  verify: "/verify",
  demo: "/demo",
  terms: "/terms",
  privacy: "/privacy",
  app: {
    home: "/app",
    welcome: "/app/welcome",
    commitments: "/app/commitments",
    createCommitment: "/app/commitments/new",
    join: "/app/join",
    score: "/app/score",
    profile: "/app/profile",
    notifications: "/app/notifications",
  },
  vendor: {
    home: "/vendor",
    redeem: "/vendor/redeem",
    history: "/vendor/history",
  },
} as const

// pages that live on the marketing website. empty when NEXT_PUBLIC_SITE_URL is unset,
// so callers can hide the link rather than point it nowhere
export const siteRoutes = {
  forBanks: env.siteUrl ? `${env.siteUrl}/for-banks` : "",
  bankLogin: env.siteUrl ? `${env.siteUrl}/bank/login` : "",
} as const
