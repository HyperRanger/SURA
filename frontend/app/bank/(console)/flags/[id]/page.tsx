import type { Metadata } from "next"
import { FlagDetailScreen } from "@/components/bank/flag-detail-screen"

export const metadata: Metadata = { title: "risk flag — sura bank console" }

// B9
export default async function BankFlagPage({ params }: PageProps<"/bank/flags/[id]">) {
  const { id } = await params
  return <FlagDetailScreen id={id} />
}
