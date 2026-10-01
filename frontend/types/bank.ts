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
  created_at: string | null
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
  score_tier?: ScoreTier
  flag_status?: FlagStatus
}

export type BankUserProfile = BankUserRow & {
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
  date_from?: string
  date_to?: string
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
  commitment_id?: string
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
