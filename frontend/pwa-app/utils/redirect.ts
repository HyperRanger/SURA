import { routes } from "@/config/routes"
import type { SelfServiceRole, UserRole } from "@/types"

// only same-origin paths, so ?next= can never bounce someone to another site
export function safeNextPath(next: string | string[] | null | undefined) {
  if (typeof next !== "string") return undefined
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return undefined
  return next
}

// carries ?next= between the auth pages so the final redirect is not lost
export function withNext(path: string, next: string | undefined) {
  return next ? `${path}?next=${encodeURIComponent(next)}` : path
}

// ?role=vendor on /signup skips the account-type question
export function parseSignupRole(role: string | string[] | undefined): SelfServiceRole | undefined {
  return role === "individual" || role === "vendor" ? role : undefined
}

// the role comes from the api's token, never from the page the person signed up on.
// a first-time member sees the welcome screen before their home
export function homeForRole(role: UserRole, { isNewAccount = false } = {}) {
  if (role === "vendor") return routes.vendor.home
  return isNewAccount ? routes.app.welcome : routes.app.home
}
