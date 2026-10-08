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
  { value: "bank:overview:read", label: "Overview" },
  { value: "bank:users:read", label: "Customers" },
  { value: "bank:commitments:read", label: "Read commitments" },
  { value: "bank:commitments:write", label: "Open and resolve lock cases" },
  { value: "bank:flags:read", label: "Read risk flags" },
  { value: "bank:flags:write", label: "Resolve flags and restrict accounts" },
  { value: "bank:audit:read", label: "Audit log" },
  { value: "bank:settlements:read", label: "Settlements" },
  { value: "bank:developer:write", label: "API keys and webhooks" },
  { value: "bank:team:write", label: "Team" },
  { value: "bank:settings:write", label: "Bank settings" },
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
  { value: "bank_admin", label: "Bank admin", description: "Everything, including team, settings and developer tools." },
  { value: "bank_risk_analyst", label: "Risk analyst", description: "Customers, locks, flags, audit and settlements." },
  { value: "bank_integration_engineer", label: "Integration engineer", description: "API keys and webhooks only." },
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
  { id: "B2", label: "Overview", href: routes.bank.home, icon: DashboardSquare01Icon, permission: "bank:overview:read" },
  { id: "B3", label: "Commitments", href: routes.bank.commitments, icon: RepeatIcon, permission: "bank:commitments:read" },
  { id: "B5", label: "Customers", href: routes.bank.users, icon: UserGroupIcon, permission: "bank:users:read" },
  { id: "B7", label: "Audit log", href: routes.bank.auditLog, icon: Audit01Icon, permission: "bank:audit:read" },
  { id: "B8", label: "Risk flags", href: routes.bank.flags, icon: Flag02Icon, permission: "bank:flags:read" },
  { id: "B10", label: "Settlements", href: routes.bank.settlements, icon: MoneyExchange01Icon, permission: "bank:settlements:read" },
  { id: "B11", label: "Developers", href: routes.bank.developers, icon: CodeIcon, permission: "bank:developer:write" },
  { id: "B12", label: "Team", href: routes.bank.team, icon: UserMultiple02Icon, permission: "bank:team:write" },
  { id: "B13", label: "Settings", href: routes.bank.settings, icon: Settings02Icon, permission: "bank:settings:write" },
  { id: "B14", label: "Account", href: routes.bank.account, icon: UserLock01Icon },
]

// the developer hub tabs, in order. the open one is kept in ?tab=
export const developerTabs = [
  { value: "api-keys", label: "API keys" },
  { value: "playground", label: "Try the API" },
  { value: "webhooks", label: "Webhooks" },
  { value: "events", label: "Events" },
  { value: "logs", label: "Logs" },
  { value: "docs", label: "Docs" },
] as const

export type DeveloperTab = (typeof developerTabs)[number]["value"]

export function isDeveloperTab(value: unknown): value is DeveloperTab {
  return developerTabs.some((tab) => tab.value === value)
}

// the commitment detail tabs, in order. the open one is kept in ?tab=
export const commitmentTabs = [
  { value: "overview", label: "Overview" },
  { value: "payouts", label: "Payouts" },
  { value: "members", label: "Members" },
  { value: "contributions", label: "Contributions" },
  { value: "support", label: "Support" },
  { value: "activity", label: "Activity" },
] as const

export type CommitmentTab = (typeof commitmentTabs)[number]["value"]

export function isCommitmentTab(value: unknown): value is CommitmentTab {
  return commitmentTabs.some((tab) => tab.value === value)
}

// the customer detail tabs, in order. flags and safety only show to roles that can read flags
export const customerTabs = [
  { value: "overview", label: "Overview" },
  { value: "commitments", label: "Commitments" },
  { value: "score-history", label: "Score history" },
  { value: "flags", label: "Flags" },
  { value: "safety", label: "Account safety" },
  { value: "activity", label: "Activity" },
] as const

export type CustomerTab = (typeof customerTabs)[number]["value"]

export function isCustomerTab(value: unknown): value is CustomerTab {
  return customerTabs.some((tab) => tab.value === value)
}

// the api scopes a machine key can hold. matches BANK_API_SCOPES in contracts.py
export const apiKeyScopes: { value: ApiKeyScope; label: string; description: string }[] = [
  { value: "score:read", label: "score:read", description: "A customer's score, tier and pillar evidence." },
  { value: "commitments:read", label: "commitments:read", description: "A customer's locks, payout slot and voucher outcome." },
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
  { value: "restricted", label: "Restrict", description: "Limits new activity while the account is reviewed." },
  { value: "suspended", label: "Suspend", description: "Stops all activity until someone reinstates it." },
  { value: "reinstated", label: "Reinstate", description: "Returns a restricted or suspended account to active." },
]

// matches PILLAR_WEIGHTS in backend/app/services/scoring.py
export const scorePillars: { key: PillarKey; label: string; weight: number }[] = [
  { key: "commitment_behaviour", label: "Commitment behaviour", weight: 0.35 },
  { key: "repayment_behaviour", label: "Repayment behaviour", weight: 0.25 },
  { key: "transaction_stability", label: "Transaction stability", weight: 0.2 },
  { key: "institutional_verification", label: "Institutional verification", weight: 0.12 },
  { key: "social_reliability", label: "Social reliability", weight: 0.08 },
]

export const MAX_SCORE = 1000

export const scoreTiers: { value: ScoreTier; label: string }[] = [
  { value: "unverified", label: "Unverified" },
  { value: "entry", label: "Entry" },
  { value: "building", label: "Building" },
  { value: "established", label: "Established" },
]

export const flagStatuses: { value: FlagStatus; label: string }[] = [
  { value: "open", label: "Open" },
  { value: "escalated", label: "Escalated" },
  { value: "confirmed", label: "Confirmed" },
  { value: "dismissed", label: "Dismissed" },
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
  { value: "dismissed", label: "Dismiss", description: "A false positive. No further action is needed." },
  { value: "confirmed", label: "Confirm", description: "The pattern is real and the evidence holds up." },
  { value: "escalated", label: "Escalate", description: "Needs a senior analyst or compliance to decide." },
]

export const commitmentStatuses = ["pending_members", "active", "under_review", "completed", "cancelled"] as const

export const settlementStatuses = ["pending", "settled", "failed", "reversed"] as const
