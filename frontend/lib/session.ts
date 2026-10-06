import { createStoredValue } from "@/lib/storage"
import type {
  AuthChallengeResponse,
  AuthTokenResponse,
  BankSessionResponse,
  PendingChallenge,
  Session,
} from "@/types"

// the signed-in account. local so it survives closing the tab
export const sessionStore = createStoredValue<Session>("local", "sura.session")

// the otp challenge in flight. session-scoped so a stale one never outlives the tab
export const challengeStore = createStoredValue<PendingChallenge>("session", "sura.auth-challenge")

// turns the api's relative timers into absolute times, so a refresh on /verify
// shows the right countdown instead of restarting it
export function rememberChallenge(
  challenge: AuthChallengeResponse,
  { phone, next, isNewAccount }: { phone: string; next?: string; isNewAccount: boolean }
) {
  const now = Date.now()
  challengeStore.write({
    challengeId: challenge.challenge_id,
    purpose: challenge.purpose,
    isNewAccount,
    phone,
    demoCode: challenge.demo_code,
    expiresAt: now + challenge.expires_in_seconds * 1000,
    resendAvailableAt: now + challenge.resend_after_seconds * 1000,
    next,
  })
}

export function startSession(token: AuthTokenResponse | BankSessionResponse) {
  sessionStore.write({
    accessToken: token.access_token,
    userId: token.user_id,
    role: token.role,
    institutionId: "institution_id" in token ? token.institution_id : undefined,
    permissions: "permissions" in token ? token.permissions : undefined,
  })
}

export function endSession() {
  sessionStore.clear()
}

export function getAccessToken() {
  return sessionStore.read()?.accessToken ?? null
}
