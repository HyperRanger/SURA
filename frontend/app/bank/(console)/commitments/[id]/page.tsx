import type { Metadata } from "next"
import { CommitmentDetailScreen } from "@/components/bank/commitment-detail-screen"
import { isCommitmentTab } from "@/config/bank"

export const metadata: Metadata = { title: "commitment — sura bank console" }

// B4. ?tab= opens a tab
export default async function BankCommitmentPage({ params, searchParams }: PageProps<"/bank/commitments/[id]">) {
  const [{ id }, { tab }] = await Promise.all([params, searchParams])
  return <CommitmentDetailScreen id={id} initialTab={isCommitmentTab(tab) ? tab : undefined} />
}
