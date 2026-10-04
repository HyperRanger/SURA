import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowUpRight01Icon, CheckmarkCircle02Icon } from "@hugeicons/core-free-icons"
import { isDemoEnabled } from "@/config/env"
import { bankGuarantees } from "@/config/for-banks"
import { routes } from "@/config/routes"
import { siteConfig } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"

export function ForBanksHero() {
  return (
    <section className="relative overflow-hidden pt-10 pb-16 md:pt-16 md:pb-24">
      <div className="container-page relative grid items-center gap-12 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <h1 className="mt-6 text-4xl leading-[1.05] font-black tracking-tight text-balance sm:text-5xl md:text-6xl">
            a savings product and a credit signal, <span className="text-link">in one api.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
            sura runs rotating savings circles on your rails and turns every on-time contribution
            into a score your credit team can audit line by line. you keep the customer, the brand
            and the money.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            {siteConfig.apiDocsUrl && (
              <a
                href={siteConfig.apiDocsUrl}
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({ size: "lg" })}
              >
                read the api docs
                <HugeiconsIcon icon={ArrowUpRight01Icon} size={20} strokeWidth={2.5} />
              </a>
            )}
            {isDemoEnabled ? (
              <Link href={routes.demo} className={buttonVariants({ variant: "outline", size: "lg" })}>
                open the bank console demo
              </Link>
            ) : (
              <a href="#contact" className={buttonVariants({ variant: "outline", size: "lg" })}>
                talk to us
              </a>
            )}
          </div>
        </div>

        <ul className="card-raised flex flex-col gap-4 rounded-[2rem] p-7">
          {bankGuarantees.map((item) => (
            <li key={item} className="flex items-start gap-3 text-[15px] leading-snug font-bold">
              <HugeiconsIcon
                icon={CheckmarkCircle02Icon}
                size={22}
                strokeWidth={2}
                className="shrink-0 text-gold"
              />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
