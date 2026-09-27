import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle02Icon } from "@hugeicons/core-free-icons"
import { bankPoints, steps } from "@/config/landing"
import { IconTile } from "@/components/shared/icon-tile"
import { SectionHeading } from "@/components/shared/section-heading"

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-cloud py-20 md:py-28">
      <div className="container-page">
        <SectionHeading
          eyebrow="how it works"
          title="from first contribution to first payout"
          description="four steps for members. the bank's app handles the screens, sura handles the rules."
        />

        <ol className="relative mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          <span
            aria-hidden="true"
            className="absolute top-5 right-[12%] left-[12%] hidden h-1 rounded-full bg-hairline-strong lg:block"
          />
          {steps.map((step, i) => (
            <li key={step.title} className="relative flex flex-col items-center text-center">
              <span className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full border-b-4 border-primary-deep bg-primary text-xl font-black text-white">
                {i + 1}
              </span>
              <div className="card-raised mt-5 flex h-full w-full flex-col items-center rounded-[2rem] p-6">
                <IconTile icon={step.icon} />
                <h3 className="mt-4 text-lg font-black">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {step.description}
                </p>
              </div>
            </li>
          ))}
        </ol>

        <div className="card-raised mt-10 grid items-center gap-8 rounded-[2rem] p-7 md:grid-cols-[1fr_1.2fr] md:p-10">
          <div>
            <p className="text-sm font-extrabold text-orange-deep dark:text-orange">
              for banks and fintechs
            </p>
            <h3 className="mt-2 text-2xl font-black tracking-tight text-balance sm:text-3xl">
              launch a savings and credit product without building underwriting from scratch
            </h3>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {bankPoints.map((point) => (
              <li
                key={point}
                className="flex items-center gap-2.5 rounded-3xl bg-cloud p-4 text-sm leading-snug font-bold"
              >
                <HugeiconsIcon
                  icon={CheckmarkCircle02Icon}
                  size={20}
                  strokeWidth={2.2}
                  className="mt-px shrink-0 text-primary"
                />
                {point}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
