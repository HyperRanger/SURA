import type { Metadata } from "next"
import { AuditLogScreen } from "@/components/bank/audit-log-screen"

export const metadata: Metadata = { title: "audit log — sura bank console" }

// B7
export default function BankAuditLogPage() {
  return <AuditLogScreen />
}
