"use client"

import { useCallback } from "react"
import { rolePermissions, type BankPermission } from "@/config/bank"
import { useStoredValue } from "@/hooks/use-stored-value"
import { sessionStore } from "@/lib/session"
import type { BankStaffRole, Session } from "@/types"

// mirrors require_bank_permission in backend/app/bank/dependencies.py: an admin
// passes every check. this only decides what to show; the api still refuses
// anything the session can't do
export function canBank(session: Session | null, permission: BankPermission | undefined) {
  if (!session) return false
  if (!permission || session.role === "bank_admin") return true
  // sessions saved before permissions were stored fall back to the role's defaults
  const granted = session.permissions ?? rolePermissions[session.role as BankStaffRole] ?? []
  return granted.includes(permission)
}

export function useBankAccess() {
  const session = useStoredValue(sessionStore)
  const can = useCallback((permission?: BankPermission) => canBank(session, permission), [session])
  return { session, can }
}
