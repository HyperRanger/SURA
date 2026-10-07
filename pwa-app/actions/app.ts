import { api } from "@/lib/api"
import { endpoints } from "@/config/endpoints"

export async function getMemberHome() { return (await api.get(endpoints.app.home)).data }
export async function getMe() { return (await api.get(endpoints.me)).data }
export async function getCommitments() { return (await api.get(endpoints.commitments)).data }
export async function getCommitment(id: string) { return (await api.get(`${endpoints.commitments}/${encodeURIComponent(id)}`)).data }
export async function getCommitmentActivity(id: string) { return (await api.get(`${endpoints.commitments}/${encodeURIComponent(id)}/activity`)).data }
export async function getVoucher(id: string, cycle: string) { return (await api.get(`${endpoints.commitments}/${encodeURIComponent(id)}/cycles/${encodeURIComponent(cycle)}/voucher`)).data }
export async function getInvitePreview(code: string) { return (await api.get(`${endpoints.commitments}/preview`, { params: { code } })).data }
export async function getVendors() { return (await api.get(endpoints.vendors)).data }
export async function resolveMember(phone: string) { return (await api.post(endpoints.app.resolveMember, { phone })).data }
export async function getVendorRecommendations(category?: string, target_amount?: number) {
  return (await api.get(endpoints.app.vendorRecommendations, { params: { category, target_amount } })).data
}
export async function getGroupHealth(commitmentId: string) {
  return (await api.get(endpoints.app.groupHealth(commitmentId))).data
}
export async function previewLock(payload: unknown) { return (await api.post(endpoints.app.lockPreview, payload)).data }
export async function createLock(payload: unknown) { return (await api.post(`${endpoints.commitments}/lock`, payload)).data }
export async function joinCommitment(invite_code: string) { return (await api.post(`${endpoints.commitments}/join`, { invite_code })).data }
export async function recordConsent(granted: boolean) { return (await api.post(endpoints.consent, { granted })).data }
export async function contribute(id: string, amount: number, event_id: string) {
  return (await api.post(`${endpoints.commitments}/${encodeURIComponent(id)}/contribute`, { amount, event_id })).data
}
export async function cancelCommitment(id: string) { return (await api.post(`${endpoints.commitments}/${encodeURIComponent(id)}/cancel`)).data }
export async function getScore(userId: string) { return (await api.get(endpoints.score(userId))).data }
export async function getScoreHistory(userId: string) { return (await api.get(endpoints.scoreHistory(userId))).data }
export async function getScoreEntry(userId: string, entryId: string) { return (await api.get(`${endpoints.scoreHistory(userId)}/${encodeURIComponent(entryId)}`)).data }
export async function getNotifications() { return (await api.get(endpoints.notifications)).data }
export async function getVendorHome() { return (await api.get(endpoints.app.vendorOverview)).data }
export async function validateVoucher(voucher_code: string) { return (await api.post(`${endpoints.vendors}/redeem/validate`, { voucher_code })).data }
export async function redeemVoucher(voucher_code: string) { return (await api.post(`${endpoints.vendors}/redeem`, { voucher_code })).data }
export async function getRedemptions() { return (await api.get(endpoints.vendorRedemptions)).data }
export async function getRedemption(id: string) { return (await api.get(`${endpoints.vendorRedemptions}/${encodeURIComponent(id)}`)).data }
export async function logout() { return (await api.post(endpoints.logout)).data }
export async function logoutAll() { return (await api.post(endpoints.logoutAll)).data }
