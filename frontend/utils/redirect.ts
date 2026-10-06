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
