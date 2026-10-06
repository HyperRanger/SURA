import type { Metadata } from "next"
import { SettlementsScreen, type SettlementScope } from "@/components/bank/settlements-screen"

export const metadata: Metadata = { title: "Settlements — Sura bank console" }

// B10
export default async function BankSettlementsPage({ searchParams }: PageProps<"/bank/settlements">) {
  const params = await searchParams
  const pick = (key: keyof SettlementScope) => (typeof params[key] === "string" ? params[key] : undefined)
  return (
    <SettlementsScreen
      initialScope={{ commitment_id: pick("commitment_id"), user_id: pick("user_id"), vendor_id: pick("vendor_id") }}
    />
  )
}
