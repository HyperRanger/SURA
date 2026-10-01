import type { Metadata } from "next"
import { UserDetailScreen } from "@/components/bank/user-detail-screen"

export const metadata: Metadata = { title: "customer — sura bank console" }

// B6
export default async function BankUserPage({ params }: PageProps<"/bank/users/[id]">) {
  const { id } = await params
  return <UserDetailScreen id={id} />
}
