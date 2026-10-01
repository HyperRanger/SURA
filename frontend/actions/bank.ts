import { api } from "@/lib/api"
import { endpoints } from "@/config/endpoints"
import type {
  AuditLogEntry,
  AuditLogFilters,
  BankCommitment,
  BankCommitmentFilters,
  BankCommitmentRow,
  BankLoginPayload,
  BankMfaChallenge,
  BankOverview,
  BankSessionResponse,
  BankUserCommitment,
  BankUserFilters,
  BankUserProfile,
  BankUserRow,
  BankUserScore,
  FlagResolutionPayload,
  RiskFlag,
  RiskFlagDetail,
  RiskFlagFilters,
  Settlement,
  SettlementFilters,
} from "@/types"

// the api reads an empty query value as a real filter, so blanks are dropped
function cleanParams<T extends object>(filters: T) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== "")
  )
}

// B1. answers with a session, or with an mfa challenge when the account has a second factor
export async function bankLogin(payload: BankLoginPayload) {
  const { data } = await api.post<BankSessionResponse | BankMfaChallenge>(endpoints.bank.login, payload)
  return data
}

export async function bankVerifyMfa(payload: { challenge_id: string; code: string }) {
  const { data } = await api.post<BankSessionResponse>(endpoints.bank.verifyMfa, payload)
  return data
}

export function isMfaChallenge(response: BankSessionResponse | BankMfaChallenge): response is BankMfaChallenge {
  return "mfa_required" in response && response.mfa_required
}

// B2
export async function getBankOverview() {
  const { data } = await api.get<BankOverview>(endpoints.bank.overview)
  return data
}

// B3
export async function listBankCommitments(filters: BankCommitmentFilters = {}) {
  const { data } = await api.get<BankCommitmentRow[]>(endpoints.bank.commitments, { params: cleanParams(filters) })
  return data
}

// B4
export async function getBankCommitment(id: string) {
  const { data } = await api.get<BankCommitment>(endpoints.bank.commitment(id))
  return data
}

// B5
export async function listBankUsers(filters: BankUserFilters = {}) {
  const { data } = await api.get<BankUserRow[]>(endpoints.bank.users, { params: cleanParams(filters) })
  return data
}

// B6. viewing a profile or score is itself recorded in the bank's audit log
export async function getBankUser(id: string) {
  const { data } = await api.get<BankUserProfile>(endpoints.bank.user(id))
  return data
}

export async function getBankUserScore(id: string) {
  const { data } = await api.get<BankUserScore>(endpoints.bank.userScore(id))
  return data
}

export async function listBankUserCommitments(id: string) {
  const { data } = await api.get<BankUserCommitment[]>(endpoints.bank.userCommitments(id))
  return data
}

export async function listBankUserFlags(id: string) {
  const { data } = await api.get<RiskFlag[]>(endpoints.bank.userFlags(id))
  return data
}

// B7
export async function getAuditLog(filters: AuditLogFilters = {}) {
  const { data } = await api.get<AuditLogEntry[]>(endpoints.bank.auditLog, { params: cleanParams(filters) })
  return data
}

// returns csv text. the export is recorded as a bank audit event
export async function exportAuditLog() {
  const { data } = await api.post<string>(endpoints.bank.auditLogExport, undefined, { responseType: "text" })
  return data
}

// B8
export async function listFlags(filters: RiskFlagFilters = {}) {
  const { data } = await api.get<RiskFlag[]>(endpoints.bank.flags, { params: cleanParams(filters) })
  return data
}

// B9
export async function getFlag(id: string) {
  const { data } = await api.get<RiskFlagDetail>(endpoints.bank.flag(id))
  return data
}

export async function resolveFlag(id: string, payload: FlagResolutionPayload) {
  const { data } = await api.post<RiskFlag>(endpoints.bank.resolveFlag(id), payload)
  return data
}

// B10
export async function listSettlements(filters: SettlementFilters = {}) {
  const { data } = await api.get<Settlement[]>(endpoints.bank.settlements, { params: cleanParams(filters) })
  return data
}
