import {
  Audit01Icon,
  CodeIcon,
  DashboardSquare01Icon,
  Flag02Icon,
  MoneyExchange01Icon,
  RepeatIcon,
  Settings02Icon,
  UserGroupIcon,
  UserLock01Icon,
  UserMultiple02Icon,
} from "@hugeicons/core-free-icons"
import type { IconSvgElement } from "@hugeicons/react"
import { routes } from "@/config/routes"
import type {
  ApiKeyScope,
  BankStaffRole,
  FlagAction,
  FlagStatus,
  PillarKey,
  RestrictionAction,
  ScoreTier,
  WebhookEvent,
} from "@/types"

// matches BANK_STAFF_ROLE_PERMISSIONS in backend/app/bank/contracts.py
export const bankPermissions = [
  { value: "bank:overview:read", label: "overview" },
  { value: "bank:users:read", label: "customers" },
  { value: "bank:commitments:read", label: "read commitments" },
  { value: "bank:commitments:write", label: "open and resolve lock cases" },
  { value: "bank:flags:read", label: "read risk flags" },
  { value: "bank:flags:write", label: "resolve flags and restrict accounts" },
  { value: "bank:audit:read", label: "audit log" },
  { value: "bank:settlements:read", label: "settlements" },
  { value: "bank:developer:write", label: "api keys and webhooks" },
  { value: "bank:team:write", label: "team" },
  { value: "bank:settings:write", label: "bank settings" },
] as const

export type BankPermission = (typeof bankPermissions)[number]["value"]

const allPermissions = bankPermissions.map((permission) => permission.value)

export const rolePermissions: Record<BankStaffRole, readonly BankPermission[]> = {
  bank_admin: allPermissions,
  bank_risk_analyst: [
    "bank:overview:read",
    "bank:users:read",
    "bank:commitments:read",
    "bank:flags:read",
    "bank:flags:write",
    "bank:audit:read",
    "bank:settlements:read",
  ],
  bank_integration_engineer: ["bank:developer:write"],
}

export const staffRoles: { value: BankStaffRole; label: string; description: string }[] = [
  { value: "bank_admin", label: "bank admin", description: "everything, including team, settings and developer tools." },
  { value: "bank_risk_analyst", label: "risk analyst", description: "customers, locks, flags, audit and settlements." },
  { value: "bank_integration_engineer", label: "integration engineer", description: "api keys and webhooks only." },
]

export type BankNavItem = {
  id: string
  label: string
  href: string
  icon: IconSvgElement
  // the api permission the section reads with. none means every bank session
  permission?: BankPermission
}

// the bank console sections, in sidebar order
export const bankNav: BankNavItem[] = [
  { id: "B2", label: "overview", href: routes.bank.home, icon: DashboardSquare01Icon, permission: "bank:overview:read" },
  { id: "B3", label: "commitments", href: routes.bank.commitments, icon: RepeatIcon, permission: "bank:commitments:read" },
  { id: "B5", label: "customers", href: routes.bank.users, icon: UserGroupIcon, permission: "bank:users:read" },
  { id: "B7", label: "audit log", href: routes.bank.auditLog, icon: Audit01Icon, permission: "bank:audit:read" },
  { id: "B8", label: "risk flags", href: routes.bank.flags, icon: Flag02Icon, permission: "bank:flags:read" },
  { id: "B10", label: "settlements", href: routes.bank.settlements, icon: MoneyExchange01Icon, permission: "bank:settlements:read" },
  { id: "B11", label: "developers", href: routes.bank.developers, icon: CodeIcon, permission: "bank:developer:write" },
  { id: "B12", label: "team", href: routes.bank.team, icon: UserMultiple02Icon, permission: "bank:team:write" },
  { id: "B13", label: "settings", href: routes.bank.settings, icon: Settings02Icon, permission: "bank:settings:write" },
  { id: "B14", label: "account", href: routes.bank.account, icon: UserLock01Icon },
]

// the api scopes a machine key can hold. matches BANK_API_SCOPES in contracts.py
export const apiKeyScopes: { value: ApiKeyScope; label: string; description: string }[] = [
  { value: "score:read", label: "score:read", description: "a customer's score, tier and pillar evidence." },
  { value: "commitments:read", label: "commitments:read", description: "a customer's locks, payout slot and voucher outcome." },
]

// matches WEBHOOK_EVENTS in contracts.py
export const webhookEvents: WebhookEvent[] = [
  "contribution.recorded",
  "cycle.paid",
  "voucher.issued",
  "voucher.redeemed",
  "score.updated",
  "flag.created",
]

export const restrictionActions: { value: RestrictionAction; label: string; description: string }[] = [
  { value: "restricted", label: "restrict", description: "limits new activity while the account is reviewed." },
  { value: "suspended", label: "suspend", description: "stops all activity until someone reinstates it." },
  { value: "reinstated", label: "reinstate", description: "returns a restricted or suspended account to active." },
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

// matches the rules in backend/app/bank/risk_rules.py, plus the seeded demo rule
export const flagRules = [
  "missed_contributions",
  "repeated_failed_logins",
  "score_decline",
  "unredeemed_voucher_expiry",
  "commitment_abandonment",
  "redemption_velocity",
  "unusual_contribution_pattern",
] as const

export const flagActions: { value: FlagAction; label: string; description: string }[] = [
  { value: "dismissed", label: "dismiss", description: "a false positive. no further action is needed." },
  { value: "confirmed", label: "confirm", description: "the pattern is real and the evidence holds up." },
  { value: "escalated", label: "escalate", description: "needs a senior analyst or compliance to decide." },
]

export const commitmentStatuses = ["pending_members", "active", "under_review", "completed", "cancelled"] as const

export const settlementStatuses = ["pending", "settled", "failed", "reversed"] as const
