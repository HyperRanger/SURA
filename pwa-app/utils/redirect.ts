import { routes } from "@/config/routes"
import type { SelfServiceRole, UserRole } from "@/types"

export function safeNextPath(next: string | string[] | null | undefined) {
  if (typeof next !== "string") return undefined
  if (!next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return undefined
  return next
}

export function withNext(path: string, next: string | undefined) {
  return next ? `${path}?next=${encodeURIComponent(next)}` : path
}

export function parseSignupRole(role: string | string[] | undefined): SelfServiceRole | undefined {
  return role === "individual" || role === "vendor" ? role : undefined
}

export function homeForRole(role: UserRole, { isNewAccount = false } = {}) {
  if (role === "vendor") return routes.vendor.home
  return isNewAccount ? routes.app.welcome : routes.app.home
}
