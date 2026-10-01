import type { Metadata } from "next"
import { CommitmentDetailScreen } from "@/components/bank/commitment-detail-screen"

export const metadata: Metadata = { title: "commitment — sura bank console" }

// B4
export default async function BankCommitmentPage({ params }: PageProps<"/bank/commitments/[id]">) {
  const { id } = await params
  return <CommitmentDetailScreen id={id} />
}
