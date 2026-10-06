import { Audiences } from "@/components/landing/audiences"
import { ClosingCta } from "@/components/landing/closing-cta"
import { Hero } from "@/components/landing/hero"
import { HowItWorks } from "@/components/landing/how-it-works"
import { Problem } from "@/components/landing/problem"
import { Score } from "@/components/landing/score"
import { VendorLock } from "@/components/landing/vendor-lock"

// P1. the problem, how a Lock works, the vendor lock and the score, then the ways in
export default function LandingPage() {
  return (
    <>
      <Hero />
      <Problem />
      <HowItWorks />
      <VendorLock />
      <Score />
      <Audiences />
      <ClosingCta />
    </>
  )
}
