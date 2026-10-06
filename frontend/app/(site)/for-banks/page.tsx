import type { Metadata } from "next"
import { ForBanksHero } from "@/components/for-banks/for-banks-hero"
import { ApiCapabilities, ApiIntegration } from "@/components/for-banks/api-overview"
import { BankContact } from "@/components/for-banks/bank-contact"

export const metadata: Metadata = {
  title: "Sura for banks — savings circles and a credit signal in one API",
  description:
    "Launch rotating savings circles under your brand and read an explainable score built from contribution history. Sura never holds funds.",
}

export default function ForBanksPage() {
  return (
    <>
      <ForBanksHero />
      <ApiCapabilities />
      <ApiIntegration />
      <BankContact />
    </>
  )
}
