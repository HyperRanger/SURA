import type { NavLink } from "@/types"
import { isDemoEnabled } from "@/config/env"
import { routes, siteRoutes } from "@/config/routes"

export const siteConfig = {
  name: "Sura",
  title: "Sura — save together, collect at a shop you trust",
  description:
    "Start a Sura Lock with people you trust. Everyone contributes on schedule, each payout goes to a vendor the group agreed on, and every on-time contribution builds your private Sura Score.",
} as const

// in-page anchors on the landing, shown in the header on wider screens
export const landingNav: NavLink[] = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Vendor lock", href: "/#vendor-lock" },
  { label: "Sura Score", href: "/#score" },
]

// links without a destination, like the bank page when the website url is unset, are dropped
export const footerLinks: NavLink[] = [
  { label: "Create account", href: routes.signup },
  { label: "Log in", href: routes.login },
  ...(isDemoEnabled ? [{ label: "Try the demo", href: routes.demo }] : []),
  { label: "Terms of use", href: routes.terms },
  { label: "Privacy", href: routes.privacy },
  { label: "For banks", href: siteRoutes.forBanks },
].filter((link) => link.href)
