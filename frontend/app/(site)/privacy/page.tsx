import type { Metadata } from "next"
import { privacyNotice } from "@/config/legal"
import { LegalDocument } from "@/components/shared/legal-document"

export const metadata: Metadata = {
  title: "Privacy notice — Sura",
  description: privacyNotice.summary,
}

export default function PrivacyPage() {
  return <LegalDocument document={privacyNotice} />
}
