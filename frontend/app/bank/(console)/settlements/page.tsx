import type { Metadata } from "next"
import { SettlementsScreen } from "@/components/bank/settlements-screen"

export const metadata: Metadata = { title: "settlements — sura bank console" }

// B10
export default async function BankSettlementsPage({ searchParams }: PageProps<"/bank/settlements">) {
  const { commitment_id } = await searchParams
  return <SettlementsScreen commitmentId={typeof commitment_id === "string" ? commitment_id : undefined} />
}
