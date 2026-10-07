import type { Metadata } from "next"
import { VerifyForm } from "@/components/auth/verify-form"

export const metadata: Metadata = {
  title: "Verify your number — Sura",
  robots: { index: false },
}

// P4
export default function VerifyPage() {
  return <VerifyForm />
}
