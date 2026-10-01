import type { IconSvgElement } from "@hugeicons/react"

export * from "./auth"

export type NavLink = {
  label: string
  href: string
}

export type Tone = "indigo" | "gold"

export type ChoiceOption<T extends string> = {
  value: T
  label: string
  description?: string
  icon?: IconSvgElement
}

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

export type LegalSection = {
  heading: string
  paragraphs?: string[]
  bullets?: string[]
}

export type LegalDocument = {
  title: string
  // iso date, e.g. 2026-10-01
  updated: string
  summary: string
  sections: LegalSection[]
}

export type ApiStatus = "checking" | "online" | "offline"

export type HealthResponse = {
  status: string
}
