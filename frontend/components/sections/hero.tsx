import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon, } from "@hugeicons/core-free-icons"
import Link from "next/link"
import { heroStats } from "@/config/landing"
import { routes } from "@/config/routes"
import { buttonVariants } from "@/components/ui/button"
import { HeroPreview } from "@/components/sections/hero-preview"

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-10 pb-16 md:pt-16 md:pb-24">

      <div className="container-page relative grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <h1 className="mt-6 text-4xl leading-[1.05] font-black tracking-tight text-balance sm:text-5xl md:text-6xl">
            save together. build a record{" "}
            <span className="text-link">banks can read.</span>
          </h1>

          <p className="mt-6 max-w-xl text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
            sura lets banks and fintechs run rotating savings circles, like ajo, with the
            rules enforced by software. payouts go straight to a vendor the group trusts,
            and every on-time contribution becomes credit history, no payslip needed.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href={routes.bank.login} title="sign in to the bank console" className={buttonVariants({ size: "lg" })}>
              open the bank console
              <HugeiconsIcon icon={ArrowRight01Icon} size={20} strokeWidth={2.5} />
            </Link>
            <Link href={routes.forBanks} className={buttonVariants({ variant: "outline", size: "lg" })}>
              see the api for banks
            </Link>
          </div>

        </div>

        <HeroPreview />
      </div>

      <div className="container-page relative mt-16 md:mt-20">
        <dl className="grid gap-4 sm:grid-cols-3">
          {heroStats.map((stat) => (
            <div key={stat.label} className="card-raised rounded-3xl p-6">
              <dt className="sr-only">{stat.label}</dt>
              <dd>
                <span className="block text-4xl font-black tracking-tight text-link">
                  {stat.value}
                </span>
                <span className="mt-2 block text-sm leading-snug font-bold">{stat.label}</span>
                <span className="mt-1 block text-xs font-semibold text-muted-foreground">
                  {stat.source}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  )
}
