import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon, Store01Icon } from "@hugeicons/core-free-icons"
import { audiences } from "@/config/landing"
import { routes } from "@/config/routes"
import { SectionHeading } from "@/components/shared/section-heading"

export function Audiences() {
  return (
    <section className="py-16 md:py-24">
      <div className="container-app">
        <SectionHeading
          title="Built for people paid in bursts"
          description="Tell us how you earn when you sign up. It shapes Sura around you, and never limits what you can do."
        />

        <ul className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          {audiences.map((audience) => (
            <li key={audience.title} className="card-raised flex flex-col gap-3 rounded-3xl p-4">
              <span className="flex size-11 items-center justify-center rounded-full bg-primary-soft text-link">
                <HugeiconsIcon icon={audience.icon} size={22} strokeWidth={2} />
              </span>
              <span>
                <span className="block font-bold">{audience.title}</span>
                <span className="block text-xs leading-snug font-semibold text-muted-foreground">
                  {audience.description}
                </span>
              </span>
            </li>
          ))}
        </ul>

        <Link
          href={`${routes.signup}?role=vendor`}
          className="group mt-4 flex items-center gap-4 rounded-3xl border-2 border-b-[5px] border-success/30 bg-success-soft p-4 transition-all hover:border-success/50 active:translate-y-0.5 active:border-b-2 md:p-5"
        >
          <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-success text-white">
            <HugeiconsIcon icon={Store01Icon} size={24} strokeWidth={2} />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block font-bold">Run a shop? Become a Sura vendor</span>
            <span className="block text-sm leading-snug font-semibold text-muted-foreground">
              Members choose you as the place their payout is collected. Redeem their vouchers at your counter in seconds.
            </span>
          </span>
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-card text-success transition-colors group-hover:bg-success group-hover:text-white">
            <HugeiconsIcon icon={ArrowRight01Icon} size={18} strokeWidth={2.5} />
          </span>
        </Link>
      </div>
    </section>
  )
}
