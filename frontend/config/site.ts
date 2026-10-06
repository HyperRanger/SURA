import type { NavLink } from "@/types"
import { env } from "@/config/env"
import { routes } from "@/config/routes"

export const siteConfig = {
  name: "sura",
  title: "sura — structured savings and credit for irregular income",
  description:
    "sura lets banks and fintechs offer rotating savings circles with enforced rules, vendor-locked payouts and a transparent score that turns on-time contributions into a credit record.",
  // placeholder inbox until the team confirms a real one
  contactEmail: "",
  apiUrl: env.apiUrl,
  apiDocsUrl: env.apiUrl ? `${env.apiUrl}/docs` : "",
} as const

// anchors are absolute so the header works on every public page, not just the landing
export const mainNav: NavLink[] = [
  { label: "features", href: "/#features" },
  { label: "how it works", href: "/#how-it-works" },
  { label: "for banks", href: routes.forBanks },
  { label: "faq", href: "/#faq" },
]

export const footerNav: { title: string; links: NavLink[] }[] = [
  {
    title: "product",
    links: [
      { label: "sura lock", href: "/#features" },
      { label: "sura score", href: "/#features" },
      { label: "how it works", href: "/#how-it-works" },
      { label: "faq", href: "/#faq" },
    ],
  },
  {
    title: "for partners",
    links: [
      { label: "bank console", href: routes.bank.login },
      { label: "the api for banks", href: routes.forBanks },
    ],
  },
  {
    title: "company",
    links: [
      { label: "for banks", href: routes.forBanks },
      { label: "terms of use", href: routes.terms },
      { label: "privacy", href: routes.privacy },
    ],
  },
]
