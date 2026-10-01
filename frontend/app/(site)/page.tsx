import { Hero } from "@/components/sections/hero"
import { Features } from "@/components/sections/features"
import { HowItWorks } from "@/components/sections/how-it-works"
import { Faq } from "@/components/sections/faq"
import { Cta } from "@/components/sections/cta"

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <HowItWorks />
      <Faq />
      <Cta />
    </>
  )
}
