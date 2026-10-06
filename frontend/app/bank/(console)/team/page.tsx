import type { Metadata } from "next"
import { TeamScreen } from "@/components/bank/team-screen"

export const metadata: Metadata = { title: "team — sura bank console" }

// B12
export default function BankTeamPage() {
  return <TeamScreen />
}
