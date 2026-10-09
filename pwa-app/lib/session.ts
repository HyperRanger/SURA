import { createStoredValue } from "@/lib/storage"
import type { AuthChallengeResponse, AuthTokenResponse, PendingChallenge, Session } from "@/types"

const DEFAULT_IDLE_TIMEOUT_MS = 5 * 60 * 1000
const ACTIVITY_PERSIST_INTERVAL_MS = 60 * 1000

// the signed-in account. local so it survives closing the app
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

export function startSession(token: AuthTokenResponse) {
  const now = Date.now()
  sessionStore.write({
    accessToken: token.access_token,
    userId: token.user_id,
    role: token.role,
    trustedDeviceToken: token.trusted_device_token ?? sessionStore.read()?.trustedDeviceToken,
    lastActivityAt: now,
    expiresAt: jwtExpiresAt(token.access_token),
  })
}

export function endSession() {
  sessionStore.clear()
}

export function getAccessToken() {
  return sessionStore.read()?.accessToken ?? null
}

function configuredIdleTimeoutMs() {
  const seconds = Number(process.env.NEXT_PUBLIC_SESSION_IDLE_TIMEOUT_SECONDS)
  return Number.isFinite(seconds) && seconds > 0 ? seconds * 1000 : DEFAULT_IDLE_TIMEOUT_MS
}

function jwtExpiresAt(token: string) {
  try {
    const payload = token.split(".")[1]
    if (!payload) return undefined
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
    const decoded = JSON.parse(atob(normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "="))) as { exp?: number }
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : undefined
  } catch {
    return undefined
  }
}

/**
 * Keeps the browser session boundary aligned with the server's idle and JWT
 * expiry rules. The API interceptor remains the authoritative fallback when a
 * server-side session ends before this browser can observe it.
 */
export function watchSessionExpiry(onExpired: () => void) {
  if (typeof window === "undefined") return () => undefined

  let timer: number | undefined
  let stopped = false
  let latestActivityAt = sessionStore.read()?.lastActivityAt ?? Date.now()

  const expire = () => {
    if (stopped || !sessionStore.read()) return
    endSession()
    onExpired()
  }

  const schedule = () => {
    if (timer) window.clearTimeout(timer)
    const session = sessionStore.read()
    if (!session) return

    const now = Date.now()
    const idleDeadline = latestActivityAt + configuredIdleTimeoutMs()
    const deadline = Math.min(idleDeadline, session.expiresAt ?? Number.POSITIVE_INFINITY)
    if (deadline <= now) {
      expire()
      return
    }
    timer = window.setTimeout(expire, deadline - now)
  }

  const recordActivity = () => {
    const session = sessionStore.read()
    if (!session) return
    const now = Date.now()
    if ((session.expiresAt ?? Number.POSITIVE_INFINITY) <= now) {
      expire()
      return
    }
    latestActivityAt = now
    if (!session.lastActivityAt || now - session.lastActivityAt >= ACTIVITY_PERSIST_INTERVAL_MS) {
      sessionStore.write({ ...session, lastActivityAt: now })
    }
    schedule()
  }

  const verifyAfterBackgrounding = () => {
    if (document.visibilityState === "visible") schedule()
  }
  const activityEvents: (keyof WindowEventMap)[] = ["pointerdown", "pointermove", "keydown", "touchstart", "scroll"]
  activityEvents.forEach((event) => window.addEventListener(event, recordActivity, { passive: true }))
  window.addEventListener("focus", verifyAfterBackgrounding)
  document.addEventListener("visibilitychange", verifyAfterBackgrounding)
  const unsubscribe = sessionStore.subscribe(() => {
    latestActivityAt = sessionStore.read()?.lastActivityAt ?? Date.now()
    schedule()
  })
  schedule()

  return () => {
    stopped = true
    if (timer) window.clearTimeout(timer)
    activityEvents.forEach((event) => window.removeEventListener(event, recordActivity))
    window.removeEventListener("focus", verifyAfterBackgrounding)
    document.removeEventListener("visibilitychange", verifyAfterBackgrounding)
    unsubscribe()
  }
}

export function redirectAfterSessionExpiry() {
  if (typeof window === "undefined") return
  endSession()
  if (window.location.pathname !== "/login") {
    window.location.replace("/login?reason=session-expired")
  }
}
