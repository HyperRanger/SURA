import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { isDemoEnabled } from "@/config/env"
import { AuthCard } from "@/components/auth/auth-card"
import { DemoSwitcher } from "@/components/demo/demo-switcher"

export const metadata: Metadata = {
  title: "try the demo — sura",
  robots: { index: false },
}

export default function DemoPage() {
  // the api refuses demo sign-ins in production too; this just hides the page
  if (!isDemoEnabled) notFound()

  return (
    <AuthCard
      title="try sura as anyone"
      description="pick a person to sign in instantly, no code needed. this page only exists outside production."
    >
      <DemoSwitcher />
    </AuthCard>
  )
}
