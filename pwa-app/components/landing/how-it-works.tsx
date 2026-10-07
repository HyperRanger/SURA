import { HugeiconsIcon } from "@hugeicons/react"
import { commitmentTypes, lockSteps } from "@/config/landing"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { IconTile } from "@/components/shared/icon-tile"
import { SectionHeading } from "@/components/shared/section-heading"

// a vertical timeline on phones, four cards in a row on desktop
export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-cloud py-16 md:py-24">
      <div className="container-app">
        <SectionHeading
          title="How a Sura Lock works"
          description="A Lock is a savings circle with the rules agreed up front and enforced for everyone."
        />

        <ol className="mt-10 flex flex-col md:mt-12 md:grid md:grid-cols-4 md:gap-5">
          {lockSteps.map((step, index) => (
            <li key={step.title} className="relative flex gap-4 pb-8 last:pb-0 md:flex-col md:pb-0">
              {index < lockSteps.length - 1 && (
                <span aria-hidden="true" className="absolute top-14 bottom-1 left-[1.375rem] w-1 rounded-full bg-hairline-strong md:hidden" />
              )}
              <span className="relative z-10 flex size-12 shrink-0 items-center justify-center rounded-full border-b-4 border-primary-deep bg-primary text-lg font-bold text-primary-foreground">
                {index + 1}
              </span>
              <div className="flex-1 pt-1 md:card-raised md:rounded-3xl md:p-6">
                <IconTile icon={step.icon} size="sm" className="hidden md:flex" />
                <h3 className="text-lg font-bold md:mt-4">{step.title}</h3>
                <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">{step.description}</p>
              </div>
            </li>
          ))}
        </ol>

        <div className="mt-12">
          <h3 className="text-sm font-bold text-muted-foreground">Lock types</h3>
          <ul className="mt-3 grid gap-3 sm:grid-cols-3">
            {commitmentTypes.map((type) => (
              <li
                key={type.title}
                className={cn(
                  "flex items-center gap-3 rounded-2xl border-2 bg-card p-3 pr-4",
                  type.available ? "border-ring/30" : "border-hairline"
                )}
              >
                <span
                  className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-full",
                    type.available ? "bg-primary text-primary-foreground" : "bg-cloud text-muted-foreground"
                  )}
                >
                  <HugeiconsIcon icon={type.icon} size={20} strokeWidth={2} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className={cn("block text-sm font-bold", !type.available && "text-muted-foreground")}>
                    {type.title}
                  </span>
                  <span className="block text-xs leading-snug font-semibold text-muted-foreground">
                    {type.description}
                  </span>
                </span>
                {type.available ? (
                  <Badge variant="success">Live</Badge>
                ) : (
                  <Badge variant="outline">Coming soon</Badge>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
