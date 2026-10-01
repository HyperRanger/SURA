import type { Metadata } from "next"
import { VerifyForm } from "@/components/auth/verify-form"

export const metadata: Metadata = {
  title: "verify your number — sura",
  robots: { index: false },
}

export default function VerifyPage() {
  return <VerifyForm />
}
