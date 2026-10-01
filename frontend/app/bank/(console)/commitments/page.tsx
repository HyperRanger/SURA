import type { Metadata } from "next"
import { CommitmentsScreen } from "@/components/bank/commitments-screen"

export const metadata: Metadata = { title: "commitments — sura bank console" }

// B3
export default function BankCommitmentsPage() {
  return <CommitmentsScreen />
}
