// shapes mirror backend/app/bank/service.py and the bank portal tags at /docs.
// every customer identifier the api returns is already masked, e.g. ••••8241

export type ScoreTier = "unverified" | "entry" | "building" | "established"

export type PillarKey =
  | "commitment_behaviour"
  | "repayment_behaviour"
  | "transaction_stability"
  | "institutional_verification"
  | "social_reliability"

export type FlagStatus = "open" | "dismissed" | "confirmed" | "escalated"

export type FlagAction = Exclude<FlagStatus, "open">

export type ScoreReport = {
  score: number
  // points per pillar; they sum exactly to the score
  breakdown: Record<PillarKey, number>
  sub_scores?: Record<PillarKey, number>
  weights?: Record<PillarKey, number>
  tier: ScoreTier
  entry_tier?: boolean
  score_version?: string
  computed_at?: string
}

export type BankOverview = {
  bank_id: string
  bank_name: string
  environment: string
  customers: number
  active_commitments: number
  total_contributed: number
  // 0 to 1
  completion_rate: number
  open_flags: number
  pending_settlements: number
  recent_settlements: {
    settlement_id: string
    commitment_id: string
    status: string
    amount: number
    redeemed_at: string | null
    simulated: boolean
  }[]
  recent_activity: {
    event_id: string
    event_type: string
    subject_id: string
    occurred_at: string | null
  }[]
}

export type BankCommitmentRow = {
  commitment_id: string
  title: string
  status: string
  type: string
  vendor_id: string
  member_count: number
  cycles: number
  current_cycle_number: number
  completed_cycle_count: number
  total_contributed: number
  created_at: string | null
}

export type BankCommitmentFilters = {
  q?: string
  status?: string
  vendor_id?: string
  member_id?: string
}

export type BankCommitment = {
  commitment_id: string
  title: string
  status: string
  type: string
  vendor: { vendor_id: string; name: string | null; verified: boolean }
  contribution_amount: number
  frequency: string
  cycles: number
  current_cycle_number: number
  completed_cycle_count: number
  // user ids in payout order, as persisted at creation
  payout_order: string[]
  members: {
    user_id: string
    name: string
    role: string
    score: number
    tier: ScoreTier
    joined_at: string | null
  }[]
  contributions: {
    contribution_id: string
    user_id: string
    cycle_number: number
    amount: number
    status: string
    paid_at: string | null
  }[]
  payout_schedule: {
    cycle_number: number
    beneficiary_id: string
    amount: number
    status: string
    voucher_status: string | null
    settlement_status: string | null
  }[]
  activity: {
    activity_id: string
    type: string
    actor_user_id: string
    cycle_number: number | null
    details: Record<string, unknown>
    occurred_at: string | null
  }[]
  support_cases: CommitmentCase[]
  created_at: string | null
}

export type CommitmentCase = {
  case_id: string
  status: "open" | "resolved"
  reason: string
  resolution_note: string | null
  opened_at: string | null
  resolved_at: string | null
}

export type CommitmentCaseResult = {
  case_id: string
  commitment_id: string
  status: "open" | "resolved"
  commitment_status: string
}

// advisory and aggregate only. it never names a member or makes a decision
export type GroupHealth = {
  commitment_id: string
  advisory: true
  group_health: "low_risk" | "medium_risk" | "high_risk"
  confidence: "limited" | "moderate" | "strong"
  reasons: string[]
  metrics: {
    commitment_status: string
    member_count: number
    joined_member_count: number
    pending_invitation_count: number
    completed_cycles: number
    missed_cycles: number
    historical_cycle_completion_rate: number | null
    current_cycle_number: number
    current_cycle_due_at: string | null
    current_cycle_grace_period_hours: number
    current_cycle_deadline_state: string
    current_cycle_required_total: number
    current_cycle_contributed_total: number
    current_cycle_paid_member_count: number
    current_cycle_partial_member_count: number
    current_cycle_unpaid_member_count: number
  }
  unavailable_signals: string[]
  policy_note: string
}

export type BankUserRow = {
  user_id: string
  name: string
  phone: string | null
  bank_customer_id: string | null
  verified: boolean
  score: number
  tier: ScoreTier
  commitments_joined: number
  active_commitments: number
  open_flags: number
  // 0 to 1, null before the first contribution
  on_time_contribution_rate: number | null
  float_eligibility: "eligible" | "locked"
}

export type BankUserFilters = {
  q?: string
  // exact match on the bank's own customer reference, not a partial search
  bank_customer_id?: string
  score_tier?: ScoreTier
  flag_status?: FlagStatus
  verified?: boolean
  float_eligibility?: "eligible" | "locked"
  commitment_status?: string
}

export type AccountStatus = "active" | "restricted" | "suspended"

export type BankUserProfile = BankUserRow & {
  account_status: AccountStatus
  restriction_reason: string | null
  source_institution: { institution_id: string; name: string } | null
  score_report: ScoreReport
  context: string | null
  score_computed_at: string | null
  score_processing_consent: boolean
  contribution_count: number
  float_eligibility_reason: string
}

export type ScoreHistoryEntry = {
  id: string
  score: number
  score_before: number | null
  event_type: string | null
  reason: string | null
  source_id: string | null
  score_version: string | null
  computed_at: string | null
  breakdown: Partial<Record<PillarKey, number>>
}

export type BankUserScore = {
  user_id: string
  current: ScoreReport
  history: ScoreHistoryEntry[]
}

export type BankUserCommitment = {
  commitment_id: string
  title: string
  status: string
  type: string
  vendor_id: string
  contribution_amount: number
  cycles: number
  completed_cycle_count: number
  member_role: string
  payout_cycle: number | null
  payout_status: string | null
  contributed_amount: number
  voucher_status: string | null
  created_at: string | null
}

export type AuditLogEntry = {
  // "score" rows are score changes, "bank_access" rows are staff actions
  type: "score" | "bank_access"
  id: string
  event_type: string | null
  user_id?: string
  reason?: string | null
  actor_id?: string
  subject_id?: string
  occurred_at: string | null
}

export type AuditLogFilters = {
  user_id?: string
  commitment_id?: string
  event_type?: string
  actor_id?: string
  date_from?: string
  date_to?: string
}

export type OverviewFilters = {
  date_from?: string
  date_to?: string
}

export type BankUserActivity = {
  type: string
  id: string
  reason?: string | null
  details?: Record<string, unknown>
  occurred_at: string | null
}

export type RestrictionAction = "restricted" | "suspended" | "reinstated"

export type RestrictionPayload = {
  action: RestrictionAction
  reason: string
  flag_id?: string
}

export type RestrictionResult = {
  user_id: string
  account_status: AccountStatus
  action: RestrictionAction
  reason: string
  restricted_by: string
  restricted_at: string | null
  restriction_id: string
}

export type Restriction = {
  restriction_id: string
  user_id: string
  action: RestrictionAction
  reason: string
  evidence: Record<string, unknown>
  flag_id: string | null
  actor_id: string
  created_at: string | null
}

export type RiskRuleRun = {
  members_evaluated: number
  rules_run: string[]
  flags_created: { flag_id: string; user_id: string; rule: string; severity: string }[]
  flags_created_count: number
}

export type RiskFlag = {
  flag_id: string
  user_id: string
  rule: string
  severity: string
  status: FlagStatus
  evidence: Record<string, unknown>
  resolution_note: string | null
  created_at: string | null
  resolved_at: string | null
}

export type RiskFlagFilters = {
  status?: FlagStatus
  severity?: string
  rule?: string
  user_id?: string
}

export type RiskFlagDetail = RiskFlag & {
  review_history: {
    event_type: string
    actor_id: string
    details: Record<string, unknown>
    occurred_at: string | null
  }[]
}

export type FlagResolutionPayload = {
  action: FlagAction
  note: string
}

export type Settlement = {
  settlement_id: string
  commitment_id: string
  vendor_id: string
  amount: number
  voucher_code: string
  status: string
  redeemed_at: string | null
  simulated: boolean
}

export type SettlementFilters = {
  q?: string
  status?: string
  vendor_id?: string
  user_id?: string
  commitment_id?: string
}

// developer hub. secrets come back once, on create or rotate, and never again
export type ApiKeyScope = "score:read" | "commitments:read"

export type ApiEnvironment = "sandbox" | "live"

export type ApiKey = {
  key_id: string
  name: string
  prefix: string
  scopes: ApiKeyScope[]
  environment: ApiEnvironment
  expires_at: string | null
  revoked_at: string | null
  last_used_at: string | null
  created_at: string | null
}

export type ApiKeyWithSecret = ApiKey & {
  secret: string
  secret_revealed_once: true
  // set when the key replaced an older one
  rotated_key_id?: string
}

export type ApiKeyPayload = {
  name: string
  scopes: ApiKeyScope[]
  environment: ApiEnvironment
  expires_at?: string
}

export type WebhookEvent =
  | "contribution.recorded"
  | "cycle.paid"
  | "voucher.issued"
  | "voucher.redeemed"
  | "score.updated"
  | "flag.created"

export type Webhook = {
  webhook_id: string
  url: string
  events: WebhookEvent[]
  status: "active" | "disabled"
  created_at: string | null
  updated_at: string | null
}

export type WebhookWithSecret = Webhook & {
  signing_secret: string
  secret_revealed_once: true
}

export type WebhookSecret = {
  webhook_id: string
  signing_secret: string
  secret_revealed_once: true
}

export type WebhookPayload = {
  url: string
  events: WebhookEvent[]
}

export type WebhookUpdatePayload = Partial<WebhookPayload> & {
  status?: Webhook["status"]
}

export type WebhookDelivery = {
  delivery_id: string
  event_id: string
  event_type: string
  attempt_number: number
  status: string
  response_status: number | null
  response_summary: string | null
  payload: Record<string, unknown>
  signature: string
  delivered_at: string | null
  created_at: string | null
}

export type WebhookEventInfo = {
  event_type: WebhookEvent
  delivery: string
  retry: string
}

export type DeveloperHome = {
  bank_id: string
  environment: ApiEnvironment
  authentication: string
  api_docs_path: string
  machine_endpoints: string[]
  webhook_delivery: string
}

// team and tenant settings
export type BankStaffRole = "bank_admin" | "bank_risk_analyst" | "bank_integration_engineer"

export type BankStaff = {
  staff_id: string
  user_id: string
  name: string | null
  email: string
  role: BankStaffRole
  permissions: string[]
  // masked to the last four digits
  mfa_phone: string | null
  status: "active" | "revoked"
  last_login_at: string | null
  created_at: string | null
}

export type BankStaffPayload = {
  name: string
  email: string
  role: BankStaffRole
  mfa_phone: string
  temporary_password: string
  permissions?: string[]
}

export type BankStaffUpdatePayload = {
  role?: BankStaffRole
  permissions?: string[]
  status?: BankStaff["status"]
}

export type BankSettings = {
  bank_id: string
  name: string
  environment: ApiEnvironment
  supported_vendor_categories: string[]
  retention_days: number
  security_settings: Record<string, unknown>
  updated_at: string | null
}

export type BankSettingsPayload = Partial<Omit<BankSettings, "bank_id" | "updated_at">>

export type ChangePasswordPayload = {
  current_password: string
  new_password: string
}

export type BankLoginPayload = {
  email: string
  password: string
}

// returned by /v1/bank/login when the account has a second factor
export type BankMfaChallenge = {
  challenge_id: string
  purpose: string
  mfa_required: true
  expires_in_seconds: number
  resend_after_seconds: number
  // only returned outside production
  demo_code?: string
}
