import type { Metadata } from "next"
import { termsOfUse } from "@/config/legal"
import { LegalDocument } from "@/components/shared/legal-document"

export const metadata: Metadata = {
  title: "Terms of use — Sura",
  description: termsOfUse.summary,
}

export default function TermsPage() {
  return <LegalDocument document={termsOfUse} />
}
