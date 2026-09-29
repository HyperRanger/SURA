import { HugeiconsIcon } from "@hugeicons/react"
import { audiences, features } from "@/config/landing"
import { IconTile } from "@/components/shared/icon-tile"
import { SectionHeading } from "@/components/shared/section-heading"

export function Features() {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="container-page">
        <SectionHeading
          title="the rules of ajo, enforced by software"
          description="sura gives a bank a ready-made savings circle product, and a fair way to lend to the people who use it."
        />

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <article
              key={feature.title}
              className="card-raised rounded-[2rem] p-7 transition-transform duration-200 hover:-translate-y-1"
            >
              <IconTile icon={feature.icon} tone={feature.tone} size="lg" />
              <h3 className="mt-5 text-xl font-black">{feature.title}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
                {feature.description}
              </p>
            </article>
          ))}
        </div>

        <div className="mt-16 rounded-[2rem] bg-cloud p-6 sm:p-8">
          <p className="text-center text-sm font-extrabold tracking-wide text-muted-foreground">
            built for people paid in bursts, and the banks that serve them
          </p>
          <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {audiences.map((audience) => (
              <li
                key={audience.title}
                className="flex items-center gap-3 rounded-full bg-card p-2 pr-5"
              >
                <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                  <HugeiconsIcon icon={audience.icon} size={22} strokeWidth={2} />
                </span>
                <span>
                  <span className="block text-sm font-black">{audience.title}</span>
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
