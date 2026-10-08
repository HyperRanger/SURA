import type { Metadata } from "next"
import { AuditLogScreen } from "@/components/bank/audit-log-screen"

export const metadata: Metadata = { title: "Audit log — Sura bank console" }

// B7
export default function BankAuditLogPage() {
  return <AuditLogScreen />
}
