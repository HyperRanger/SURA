import type { IconSvgElement } from "@hugeicons/react"

export type NavLink = {
  label: string
  href: string
}

export type Tone = "indigo" | "gold"

export type Feature = {
  title: string
  description: string
  icon: IconSvgElement
  tone: Tone
}

export type Step = {
  title: string
  description: string
  icon: IconSvgElement
}

export type Faq = {
  question: string
  answer: string
}

export type Audience = {
  title: string
  description: string
  icon: IconSvgElement
}

export type ApiStatus = "checking" | "online" | "offline"

export type HealthResponse = {
  status: string
}
