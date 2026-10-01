import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowUpRight01Icon } from "@hugeicons/core-free-icons"
import { siteConfig } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"

const contactHref = siteConfig.contactEmail
  ? `mailto:${siteConfig.contactEmail}?subject=sura%20for%20banks`
  : undefined

export function BankContact() {
  return (
    <section id="contact" className="py-20 md:py-28">
      <div className="container-page">
        <div className="rounded-[2.5rem] border-b-8 border-primary-deep bg-primary px-6 py-14 text-center text-primary-foreground sm:px-12 md:py-20">
          <h2 className="mx-auto max-w-2xl text-3xl font-black tracking-tight text-balance sm:text-4xl md:text-5xl">
            see sura on your own rails
          </h2>
          <p className="mx-auto mt-4 max-w-xl leading-relaxed text-primary-foreground/85 sm:text-lg">
            we&apos;re running first pilots with a small group of banks and fintechs. tell us about
            your customers and we&apos;ll walk you through a live integration.
          </p>
          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
            {contactHref && (
              <a href={contactHref} className={buttonVariants({ variant: "gold", size: "lg" })}>
                contact the team
              </a>
            )}
            {siteConfig.apiDocsUrl && (
              <a
                href={siteConfig.apiDocsUrl}
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({ variant: "inverse", size: "lg" })}
              >
                browse the api docs
                <HugeiconsIcon icon={ArrowUpRight01Icon} size={20} strokeWidth={2.5} />
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
