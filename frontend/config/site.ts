import type { NavLink } from "@/types"

export const siteConfig = {
  name: "sura",
  title: "sura — structured savings and credit for irregular income",
  description:
    "sura lets banks and fintechs offer rotating savings circles with enforced rules, vendor-locked payouts and a transparent score that turns on-time contributions into a credit record.",
  // placeholder inbox until the team confirms a real one
  contactEmail: "",
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "",
} as const

export const mainNav: NavLink[] = [
  { label: "features", href: "#features" },
  { label: "how it works", href: "#how-it-works" },
  { label: "faq", href: "#faq" },
]

export const footerNav: { title: string; links: NavLink[] }[] = [
  {
    title: "product",
    links: [
      { label: "sura lock", href: "#features" },
      { label: "sura score", href: "#features" },
      { label: "how it works", href: "#how-it-works" },
      { label: "faq", href: "#faq" },
    ],
  },
  {
    title: "company",
    links: [
      { label: "partner with us", href: `mailto:${siteConfig.contactEmail}` },
      { label: "contact", href: `mailto:${siteConfig.contactEmail}` },
    ],
  },
]
