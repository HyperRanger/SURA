import { problems } from "@/config/landing"
import { IconTile } from "@/components/shared/icon-tile"
import { SectionHeading } from "@/components/shared/section-heading"

export function Problem() {
  return (
    <section id="why" className="py-16 md:py-24">
      <div className="container-app">
        <SectionHeading
          eyebrow="Why Sura"
          title="Saving on irregular income is hard enough"
          description="Ajo and esusu work because people keep each other accountable. They break when trust is all that holds them together."
        />

        <ul className="mt-8 grid gap-4 md:mt-12 md:grid-cols-3 md:gap-5">
          {problems.map((problem) => (
            <li key={problem.title} className="card-raised flex gap-4 rounded-3xl p-5 md:flex-col md:p-6">
              <IconTile icon={problem.icon} tone="gold" />
              <div>
                <h3 className="text-lg font-bold">{problem.title}</h3>
                <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">{problem.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
