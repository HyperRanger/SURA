import type { NavLink } from "@/types"
import { env } from "@/config/env"
import { routes } from "@/config/routes"

export const siteConfig = {
  name: "Sura",
  title: "Sura — structured savings and credit for irregular income",
  description:
    "Sura lets banks and fintechs offer rotating savings circles with enforced rules, vendor-locked payouts and a transparent score that turns on-time contributions into a credit record.",
  // placeholder inbox until the team confirms a real one
  contactEmail: "",
  apiUrl: env.apiUrl,
  apiDocsUrl: env.apiUrl ? `${env.apiUrl}/docs` : "",
} as const

// anchors are absolute so the header works on every public page, not just the landing
export const mainNav: NavLink[] = [
  { label: "Features", href: "/#features" },
  { label: "How it works", href: "/#how-it-works" },
  { label: "For banks", href: routes.forBanks },
  { label: "FAQ", href: "/#faq" },
]

export const footerNav: { title: string; links: NavLink[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Sura Lock", href: "/#features" },
      { label: "Sura Score", href: "/#features" },
      { label: "How it works", href: "/#how-it-works" },
      { label: "FAQ", href: "/#faq" },
    ],
  },
  {
    title: "For partners",
    links: [
      { label: "Bank console", href: routes.bank.login },
      { label: "The API for banks", href: routes.forBanks },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "For banks", href: routes.forBanks },
      { label: "Terms of use", href: routes.terms },
      { label: "Privacy", href: routes.privacy },
    ],
  },
]
