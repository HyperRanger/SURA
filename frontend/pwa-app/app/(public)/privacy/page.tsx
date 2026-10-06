import type { Metadata } from "next"
import { privacyNotice } from "@/config/legal"
import { LegalDocument } from "@/components/shared/legal-document"

export const metadata: Metadata = {
  title: "Privacy notice — Sura",
  description: privacyNotice.summary,
}

// P6. includes how the score is processed and who can see it
export default function PrivacyPage() {
  return <LegalDocument document={privacyNotice} />
}
