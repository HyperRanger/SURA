import axios from "axios"
import { api } from "@/lib/api"
import { env } from "@/config/env"
import { endpoints } from "@/config/endpoints"
import type {
  ApiKey,
  ApiKeyPayload,
  ApiKeyWithSecret,
  AuditLogEntry,
  AuditLogFilters,
  BankCommitment,
  BankCommitmentFilters,
  BankCommitmentRow,
  BankLoginPayload,
  BankMfaChallenge,
  BankOverview,
  BankSessionResponse,
  BankSettings,
  BankSettingsPayload,
  BankStaff,
  BankStaffPayload,
  BankStaffUpdatePayload,
  BankUserActivity,
  BankUserCommitment,
  BankUserFilters,
  BankUserProfile,
  BankUserRow,
  BankUserScore,
  ChangePasswordPayload,
  CommitmentCaseResult,
  DeveloperHome,
  FlagResolutionPayload,
  GroupHealth,
  OverviewFilters,
  Restriction,
  RestrictionPayload,
  RestrictionResult,
  RiskFlag,
  RiskFlagDetail,
  RiskFlagFilters,
  RiskRuleRun,
  Settlement,
  SettlementFilters,
  Webhook,
  WebhookDelivery,
  WebhookEventInfo,
  WebhookPayload,
  WebhookSecret,
  WebhookUpdatePayload,
  WebhookWithSecret,
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

// revokes the token server side, so a copy of it stops working too. idempotent.
// takes the token so the caller can clear the local session without waiting
export async function bankLogout(accessToken: string) {
  const { data } = await api.post<{ status: string }>(endpoints.bank.logout, undefined, {
    timeout: 10_000,
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return data
}

// ends every session this staff member holds, including the current one
export async function changeBankPassword(payload: ChangePasswordPayload) {
  const { data } = await api.post<{ status: string; sessions_revoked: boolean }>(endpoints.bank.password, payload)
  return data
}

// B2
export async function getBankOverview(filters: OverviewFilters = {}) {
  const { data } = await api.get<BankOverview>(endpoints.bank.overview, { params: cleanParams(filters) })
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

// advisory and aggregate. never a lending decision
export async function getCommitmentGroupHealth(id: string) {
  const { data } = await api.get<GroupHealth>(endpoints.bank.commitmentGroupHealth(id))
  return data
}

// puts the lock under review until the case is resolved
export async function openCommitmentCase(id: string, reason: string) {
  const { data } = await api.post<CommitmentCaseResult>(endpoints.bank.commitmentCases(id), { reason })
  return data
}

export async function resolveCommitmentCase(id: string, caseId: string, note: string) {
  const { data } = await api.post<CommitmentCaseResult>(endpoints.bank.resolveCommitmentCase(id, caseId), { note })
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

export async function listBankUserActivity(id: string) {
  const { data } = await api.get<BankUserActivity[]>(endpoints.bank.userActivity(id))
  return data
}

export async function listBankUserFlags(id: string) {
  const { data } = await api.get<RiskFlag[]>(endpoints.bank.userFlags(id))
  return data
}

export async function listBankUserRestrictions(id: string) {
  const { data } = await api.get<Restriction[]>(endpoints.bank.userRestrictions(id))
  return data
}

// an explicit human decision, written to the audit trail
export async function applyBankUserRestriction(id: string, payload: RestrictionPayload) {
  const { data } = await api.post<RestrictionResult>(endpoints.bank.userRestriction(id), payload)
  return data
}

export async function revokeBankUserSessions(id: string) {
  const { data } = await api.post<{ user_id: string; sessions_revoked: boolean; at: string }>(
    endpoints.bank.userRevokeSessions(id)
  )
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

// opens flags only. it never restricts an account by itself
export async function runRiskRules(userIds: string[] | null = null) {
  const { data } = await api.post<RiskRuleRun>(endpoints.bank.runRiskRules, { user_ids: userIds })
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

// B11. developer hub

export type IntegrationResponse = { status: number; durationMs: number; body: unknown }

// a real machine request, as the bank's own server would make it. it skips the shared
// client on purpose: no staff bearer token rides along, only the api key, and any
// status comes back as a result, since a 401 or 403 is worth seeing in a playground
export async function callIntegration(path: string, apiKey: string): Promise<IntegrationResponse> {
  const started = performance.now()
  const response = await axios.get(path, {
    baseURL: env.apiUrl,
    timeout: 30_000,
    headers: { "X-Sura-API-Key": apiKey },
    validateStatus: () => true,
  })
  return { status: response.status, durationMs: Math.round(performance.now() - started), body: response.data }
}

export async function getDeveloperHome() {
  const { data } = await api.get<DeveloperHome>(endpoints.bank.developers)
  return data
}

export async function listApiKeys() {
  const { data } = await api.get<ApiKey[]>(endpoints.bank.apiKeys)
  return data
}

export async function createApiKey(payload: ApiKeyPayload) {
  const { data } = await api.post<ApiKeyWithSecret>(endpoints.bank.apiKeys, payload)
  return data
}

// revokes the old key and returns a new one with the same name and scopes
export async function rotateApiKey(id: string) {
  const { data } = await api.post<ApiKeyWithSecret>(endpoints.bank.rotateApiKey(id))
  return data
}

export async function revokeApiKey(id: string) {
  await api.delete(endpoints.bank.apiKey(id))
}

export async function listWebhooks() {
  const { data } = await api.get<Webhook[]>(endpoints.bank.webhooks)
  return data
}

export async function createWebhook(payload: WebhookPayload) {
  const { data } = await api.post<WebhookWithSecret>(endpoints.bank.webhooks, payload)
  return data
}

export async function updateWebhook(id: string, payload: WebhookUpdatePayload) {
  const { data } = await api.patch<Webhook>(endpoints.bank.webhook(id), payload)
  return data
}

export async function disableWebhook(id: string) {
  await api.delete(endpoints.bank.webhook(id))
}

// a signed, simulated delivery. no request leaves sura
export async function testWebhook(id: string) {
  const { data } = await api.post<WebhookDelivery>(endpoints.bank.testWebhook(id))
  return data
}

export async function rotateWebhookSecret(id: string) {
  const { data } = await api.post<WebhookSecret>(endpoints.bank.rotateWebhookSecret(id))
  return data
}

export async function listWebhookDeliveries(id: string) {
  const { data } = await api.get<WebhookDelivery[]>(endpoints.bank.webhookDeliveries(id))
  return data
}

export async function listWebhookEvents() {
  const { data } = await api.get<WebhookEventInfo[]>(endpoints.bank.events)
  return data
}

// team
export async function listBankStaff() {
  const { data } = await api.get<BankStaff[]>(endpoints.bank.team)
  return data
}

export async function createBankStaff(payload: BankStaffPayload) {
  const { data } = await api.post<BankStaff>(endpoints.bank.team, payload)
  return data
}

export async function updateBankStaff(id: string, payload: BankStaffUpdatePayload) {
  const { data } = await api.patch<BankStaff>(endpoints.bank.staff(id), payload)
  return data
}

export async function resetBankStaffPassword(id: string, newPassword: string) {
  const { data } = await api.post<{ status: string; staff_id: string }>(endpoints.bank.staffPasswordReset(id), {
    new_password: newPassword,
  })
  return data
}

export async function setBankStaffPermissions(id: string, permissions: string[]) {
  const { data } = await api.put<{ staff_id: string; permissions: string[] }>(endpoints.bank.staffPermissions(id), {
    permissions,
  })
  return data
}

// settings
export async function getBankSettings() {
  const { data } = await api.get<BankSettings>(endpoints.bank.settings)
  return data
}

export async function updateBankSettings(payload: BankSettingsPayload) {
  const { data } = await api.patch<BankSettings>(endpoints.bank.settings, payload)
  return data
}
