import type { Metadata } from "next"
import { SettingsScreen } from "@/components/bank/settings-screen"

export const metadata: Metadata = { title: "Settings — Sura bank console" }

// B13
export default function BankSettingsPage() {
  return <SettingsScreen />
}
