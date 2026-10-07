import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { isDemoEnabled } from "@/config/env"
import { AuthCard } from "@/components/auth/auth-card"
import { DemoSwitcher } from "@/components/demo/demo-switcher"

export const metadata: Metadata = {
  title: "Try the demo — Sura",
  robots: { index: false },
}

// P8
export default function DemoPage() {
  // the api refuses demo sign-ins in production too; this just hides the page
  if (!isDemoEnabled) notFound()

  return (
    <AuthCard
      className="max-w-xl"
      title="Try Sura as anyone"
      description="Pick a person to sign in instantly, no code needed. This page only exists outside production."
    >
      <DemoSwitcher />
    </AuthCard>
  )
}
