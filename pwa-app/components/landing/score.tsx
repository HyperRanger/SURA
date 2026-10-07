import { HugeiconsIcon } from "@hugeicons/react"
import { Tick02Icon } from "@hugeicons/core-free-icons"
import { scorePoints } from "@/config/landing"
import { ScorePreview } from "@/components/landing/score-preview"
import { SectionHeading } from "@/components/shared/section-heading"

export function Score() {
  return (
    <section id="score" className="bg-cloud py-16 md:py-24">
      <div className="container-app grid items-center gap-10 md:grid-cols-2 md:gap-14">
        <div>
          <SectionHeading
            eyebrow="Sura Score"
            title="A score that's yours, and only yours"
            description="Every on-time contribution and completed Lock grows your Sura Score. With your consent, the bank that offers Sura can use it to offer you credit, no payslip needed."
          />
          <ul className="mt-7 flex flex-col gap-4">
            {scorePoints.map((point) => (
              <li key={point.title} className="flex items-start gap-3">
                <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <HugeiconsIcon icon={Tick02Icon} size={15} strokeWidth={3} />
                </span>
                <span>
                  <span className="block font-bold">{point.title}</span>
                  <span className="block text-[15px] leading-relaxed text-muted-foreground">{point.description}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <ScorePreview />
      </div>
    </section>
  )
}
