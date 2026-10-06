import { HugeiconsIcon } from "@hugeicons/react"
import { audiences, features } from "@/config/landing"
import { FeatureCard } from "@/components/shared/feature-card"
import { SectionHeading } from "@/components/shared/section-heading"

export function Features() {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="container-page">
        <SectionHeading
          title="The rules of ajo, enforced by software"
          description="Sura gives a bank a ready-made savings circle product, and a fair way to lend to the people who use it."
        />

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <FeatureCard key={feature.title} feature={feature} />
          ))}
        </div>

        <div className="mt-16 rounded-[2rem] bg-cloud p-6 sm:p-8">
          <p className="text-center text-sm font-bold tracking-wide text-muted-foreground">
            Built for people paid in bursts, and the banks that serve them
          </p>
          <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {audiences.map((audience) => (
              <li
                key={audience.title}
                className="flex items-center gap-3 rounded-full bg-card p-2 pr-5"
              >
                <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <HugeiconsIcon icon={audience.icon} size={22} strokeWidth={2} />
                </span>
                <span>
                  <span className="block text-sm font-bold">{audience.title}</span>
                  <span className="block text-xs leading-snug font-semibold text-muted-foreground">
                    {audience.description}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
