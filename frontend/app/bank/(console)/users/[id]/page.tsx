import type { Metadata } from "next"
import { UserDetailScreen } from "@/components/bank/user-detail-screen"
import { isCustomerTab } from "@/config/bank"

export const metadata: Metadata = { title: "customer — sura bank console" }

// B6. ?tab= opens a tab
export default async function BankUserPage({ params, searchParams }: PageProps<"/bank/users/[id]">) {
  const [{ id }, { tab }] = await Promise.all([params, searchParams])
  return <UserDetailScreen id={id} initialTab={isCustomerTab(tab) ? tab : undefined} />
}
