import type { Metadata } from "next"
import { FlagsScreen } from "@/components/bank/flags-screen"

export const metadata: Metadata = { title: "risk flags — sura bank console" }

// B8
export default function BankFlagsPage() {
  return <FlagsScreen />
}
