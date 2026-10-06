import type { Metadata } from "next"
import { AccountScreen } from "@/components/bank/account-screen"

export const metadata: Metadata = { title: "Your account — Sura bank console" }

// B14
export default function BankAccountPage() {
  return <AccountScreen />
}
