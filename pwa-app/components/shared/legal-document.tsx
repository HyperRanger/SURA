import { routes } from "@/config/routes"
import type { LegalDocument as LegalDocumentData } from "@/types"
import { BackButton } from "@/components/shared/back-button"
import { LegalContents } from "@/components/shared/legal-contents"
import { formatDate } from "@/utils/format"

const slug = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")

// renders a static policy page (P5, P6) from config: a header, then a sticky contents sidebar beside the sections
export function LegalDocument({ document }: { document: LegalDocumentData }) {
  const contents = document.sections.map((section) => ({ id: slug(section.heading), heading: section.heading }))

  return (
    <div className="container-app py-10 md:py-16">
      <header className="max-w-3xl">
        <BackButton fallbackHref={routes.home} className="-ml-2" />
        <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl">{document.title}</h1>
        <p className="mt-6 text-base leading-relaxed font-semibold text-pretty text-muted-foreground sm:text-lg">
          {document.summary}
        </p>
        <p className="mt-4 text-sm font-bold text-muted-foreground">
          Last updated <time dateTime={document.updated}>{formatDate(document.updated)}</time>
        </p>
      </header>

      <div className="mt-10 grid gap-10 border-t border-border pt-10 lg:mt-14 lg:grid-cols-[16rem_minmax(0,1fr)] lg:gap-16 lg:pt-14">
        <aside>
          <LegalContents items={contents} />
        </aside>

        <article className="flex max-w-3xl flex-col gap-12">
          {document.sections.map((section, index) => (
            <section key={section.heading} id={contents[index].id} className="scroll-mt-28">
              <h2 className="text-xl font-bold tracking-tight sm:text-2xl">
                <span className="text-gold-deep">{index + 1}.</span> {section.heading}
              </h2>
              {section.paragraphs?.map((paragraph) => (
                <p key={paragraph} className="mt-3 leading-relaxed text-pretty text-muted-foreground">
                  {paragraph}
                </p>
              ))}
              {section.bullets && (
                <ul className="mt-3 flex list-disc flex-col gap-2 pl-5 leading-relaxed text-muted-foreground marker:text-gold">
                  {section.bullets.map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </article>
      </div>
    </div>
  )
}
