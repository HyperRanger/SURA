import type { Metadata } from "next"
import { FlagsScreen } from "@/components/bank/flags-screen"

export const metadata: Metadata = { title: "Risk flags — Sura bank console" }

// B8
export default function BankFlagsPage() {
  return <FlagsScreen />
}
