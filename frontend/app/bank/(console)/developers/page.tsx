import type { Metadata } from "next"
import { DevelopersScreen } from "@/components/bank/developers-screen"
import { isDeveloperTab } from "@/config/bank"

export const metadata: Metadata = { title: "developers — sura bank console" }

// B11. ?tab= opens a tab, and ?webhook= picks the endpoint on the logs tab
export default async function BankDevelopersPage({ searchParams }: PageProps<"/bank/developers">) {
  const { tab, webhook } = await searchParams
  return (
    <DevelopersScreen
      initialTab={isDeveloperTab(tab) ? tab : undefined}
      initialWebhookId={typeof webhook === "string" ? webhook : undefined}
    />
  )
}
