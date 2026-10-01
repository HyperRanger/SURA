import { routes } from "@/config/routes"
import type { LegalDocument as LegalDocumentData } from "@/types"
import { BackButton } from "@/components/shared/back-button"
import { formatDate } from "@/utils/format"

const slug = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")

// renders a static policy page (P5, P6) from config, with an in-page contents list
export function LegalDocument({ document }: { document: LegalDocumentData }) {
  return (
    <div className="container-page">
      <article className="mx-auto max-w-3xl py-10 md:py-16">
        <BackButton fallbackHref={routes.home} className="-ml-2" />

        <header className="mt-6">
          <h1 className="text-4xl font-black tracking-tight sm:text-5xl">{document.title}</h1>
          <p className="mt-3 text-sm font-bold text-muted-foreground">
            last updated <time dateTime={document.updated}>{formatDate(document.updated)}</time>
          </p>
          <p className="mt-6 text-base leading-relaxed font-semibold text-pretty text-muted-foreground sm:text-lg">
            {document.summary}
          </p>
        </header>

        <nav aria-label="contents" className="card-raised mt-8 rounded-3xl p-5">
          <h2 className="text-xs font-extrabold tracking-wider text-gold-deep">on this page</h2>
          <ol className="mt-3 grid gap-2 sm:grid-cols-2">
            {document.sections.map((section, index) => (
              <li key={section.heading}>
                <a
                  href={`#${slug(section.heading)}`}
                  className="text-sm font-bold text-link underline-offset-4 hover:underline"
                >
                  {index + 1}. {section.heading}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="mt-10 flex flex-col gap-10">
          {document.sections.map((section, index) => (
            <section key={section.heading} id={slug(section.heading)} className="scroll-mt-28">
              <h2 className="text-xl font-black tracking-tight sm:text-2xl">
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
        </div>
      </article>
    </div>
  )
}
