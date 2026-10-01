import { routes } from "@/config/routes"
import type { UserRole } from "@/types"

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

export function isBankRole(role: UserRole) {
  return role === "bank" || role.startsWith("bank_")
}

// where a freshly signed-in person lands. new members see the welcome cards (M2),
// returning members go straight home (M1)
export function homeForRole(role: UserRole, { isNewAccount = false } = {}) {
  if (role === "vendor") return routes.vendor.home
  if (isBankRole(role)) return routes.bank.home
  return isNewAccount ? routes.member.welcome : routes.member.home
}
