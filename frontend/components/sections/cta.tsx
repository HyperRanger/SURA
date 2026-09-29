import { siteConfig } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"

export function Cta() {
  return (
    <section id="get-started" className="pb-20 md:pb-28">
      <div className="container-page">
        <div className="relative overflow-hidden rounded-[2.5rem] border-b-8 border-primary-deep bg-primary px-6 py-14 text-center text-white sm:px-12 md:py-20">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -top-24 -left-24 size-72 rounded-full bg-white/10"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-16 -bottom-28 size-80 rounded-full bg-orange/30"
          />

          <div className="relative mx-auto max-w-2xl">
            <h2 className="text-3xl font-black tracking-tight text-balance sm:text-4xl md:text-5xl">
              bring sura to your customers
            </h2>
            <p className="mt-4 text-base leading-relaxed text-white/85 sm:text-lg">
              we&apos;re working with a small group of banks and fintechs on our first
              pilots. tell us about your product and we&apos;ll show you sura running end
              to end.
            </p>
            <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
              <a
                href={`mailto:${siteConfig.contactEmail}?subject=sura%20demo%20request`}
                className={buttonVariants({ variant: "inverse", size: "lg" })}
              >
                request a demo
              </a>
              <a href="#faq" className={buttonVariants({ variant: "orange", size: "lg" })}>
                read the faq
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
