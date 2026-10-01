import {
  Audit01Icon,
  CodeIcon,
  DashboardSquare01Icon,
  Flag02Icon,
  MoneyExchange01Icon,
  RepeatIcon,
  UserGroupIcon,
} from "@hugeicons/core-free-icons"
import type { IconSvgElement } from "@hugeicons/react"
import { routes } from "@/config/routes"
import type { FlagAction, FlagStatus, PillarKey, ScoreTier } from "@/types"

export type BankNavItem = {
  id: string
  label: string
  href: string
  icon: IconSvgElement
}

// the bank console sections, in sidebar order
export const bankNav: BankNavItem[] = [
  { id: "B2", label: "overview", href: routes.bank.home, icon: DashboardSquare01Icon },
  { id: "B3", label: "commitments", href: routes.bank.commitments, icon: RepeatIcon },
  { id: "B5", label: "customers", href: routes.bank.users, icon: UserGroupIcon },
  { id: "B7", label: "audit log", href: routes.bank.auditLog, icon: Audit01Icon },
  { id: "B8", label: "risk flags", href: routes.bank.flags, icon: Flag02Icon },
  { id: "B10", label: "settlements", href: routes.bank.settlements, icon: MoneyExchange01Icon },
  { id: "B11", label: "developers", href: routes.bank.developers, icon: CodeIcon },
]

// matches PILLAR_WEIGHTS in backend/app/services/scoring.py
export const scorePillars: { key: PillarKey; label: string; weight: number }[] = [
  { key: "commitment_behaviour", label: "commitment behaviour", weight: 0.35 },
  { key: "repayment_behaviour", label: "repayment behaviour", weight: 0.25 },
  { key: "transaction_stability", label: "transaction stability", weight: 0.2 },
  { key: "institutional_verification", label: "institutional verification", weight: 0.12 },
  { key: "social_reliability", label: "social reliability", weight: 0.08 },
]

export const MAX_SCORE = 1000

export const scoreTiers: { value: ScoreTier; label: string }[] = [
  { value: "unverified", label: "unverified" },
  { value: "entry", label: "entry" },
  { value: "building", label: "building" },
  { value: "established", label: "established" },
]

export const flagStatuses: { value: FlagStatus; label: string }[] = [
  { value: "open", label: "open" },
  { value: "escalated", label: "escalated" },
  { value: "confirmed", label: "confirmed" },
  { value: "dismissed", label: "dismissed" },
]

export const flagSeverities = ["low", "medium", "high"] as const

export const flagActions: { value: FlagAction; label: string; description: string }[] = [
  { value: "dismissed", label: "dismiss", description: "a false positive. no further action is needed." },
  { value: "confirmed", label: "confirm", description: "the pattern is real and the evidence holds up." },
  { value: "escalated", label: "escalate", description: "needs a senior analyst or compliance to decide." },
]

export const commitmentStatuses = ["pending_members", "active", "completed", "cancelled"] as const

export const settlementStatuses = ["pending", "settled", "failed", "reversed"] as const
