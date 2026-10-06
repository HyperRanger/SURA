import type { Metadata } from "next"
import type { ReactNode } from "react"
import { BankShell } from "@/components/bank/bank-shell"

export const metadata: Metadata = {
  title: "bank console — sura",
  robots: { index: false },
}

// B2 to B14. each section shows only when the session holds its permission
export default function BankConsoleLayout({ children }: { children: ReactNode }) {
  return <BankShell>{children}</BankShell>
}
