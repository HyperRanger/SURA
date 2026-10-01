import type { Metadata } from "next"
import { DevelopersScreen } from "@/components/bank/developers-screen"

export const metadata: Metadata = { title: "developers — sura bank console" }

// B11
export default function BankDevelopersPage() {
  return <DevelopersScreen />
}
