import { BankIcon, LaptopIcon, Store01Icon, StudentIcon, Ticket01Icon } from "@hugeicons/core-free-icons"
import type { IconSvgElement } from "@hugeicons/react"
import { env } from "@/config/env"
import { siteRoutes } from "@/config/routes"

// how a persona signs in. the first two map to one non-production api route each
export type DemoSignIn =
  // POST /v1/auth/demo-token, for the named people in the seeded story
  | { type: "seeded-user"; userId: string }
  // POST /v1/demo/login-as, a generic account per role
  | { type: "role"; role: "individual" | "vendor" }
  // the bank console lives on the website, which has its own one-tap demo sign in
  | { type: "external"; href: string }

export type DemoArea = "member" | "vendor" | "bank"

export type DemoPersona = {
  id: string
  name: string
  tagline: string
  description: string
  area: DemoArea
  icon: IconSvgElement
  signIn: DemoSignIn
}

// matches backend/app/services/demo_data.py. amara and tunde share the
// "laptop fund" rotation: cycle 1 is redeemed by amara, cycle 2 waits on tunde
export const demoPersonas: DemoPersona[] = [
  {
    id: "amara",
    name: "Amara Okafor",
    tagline: "Student",
    description: "Created the Laptop Fund and already redeemed cycle 1.",
    area: "member",
    icon: StudentIcon,
    signIn: { type: "seeded-user", userId: "usr_demo_amara" },
  },
  {
    id: "tunde",
    name: "Tunde Adeyemi",
    tagline: "Trader",
    description: "Next in line for a payout, but still owes this cycle.",
    area: "member",
    icon: Store01Icon,
    signIn: { type: "seeded-user", userId: "usr_demo_tunde" },
  },
  {
    id: "member",
    name: "New member",
    tagline: "Freelancer",
    description: "A fresh account with no history, to create or join a Lock.",
    area: "member",
    icon: LaptopIcon,
    signIn: { type: "role", role: "individual" },
  },
  {
    id: "vendor",
    name: "Demo vendor",
    tagline: "Vendor terminal",
    description: "The counter view, where Sura vouchers are checked and redeemed.",
    area: "vendor",
    icon: Ticket01Icon,
    signIn: { type: "role", role: "vendor" },
  },
  {
    id: "bank",
    name: "Demo bank",
    tagline: "Bank console",
    description: "Opens the bank console on the Sura website, where the demo bank signs in.",
    area: "bank",
    icon: BankIcon,
    signIn: { type: "external", href: siteRoutes.bankLogin },
  },
]

export const demoAreas: { area: DemoArea; title: string }[] = [
  { area: "member", title: "Members" },
  { area: "vendor", title: "Vendor" },
  { area: "bank", title: "Bank" },
]

// the named people need the backend's demo otp code, and the bank needs the
// website's address. without them those personas are hidden
export function isPersonaAvailable(persona: DemoPersona) {
  if (persona.signIn.type === "seeded-user") return Boolean(env.demoOtpCode)
  if (persona.signIn.type === "external") return Boolean(persona.signIn.href)
  return true
}
