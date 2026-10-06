import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowUpRight01Icon } from "@hugeicons/core-free-icons"
import { routes, siteRoutes } from "@/config/routes"
import { buttonVariants } from "@/components/ui/button"

export function ClosingCta() {
  return (
    <section className="pb-16 md:pb-24">
      <div className="container-app">
        <div className="card-raised hero-glow rounded-[2rem] px-5 py-10 text-center sm:px-10 md:py-16">
          <h2 className="mx-auto max-w-xl text-3xl font-bold tracking-tight text-balance sm:text-4xl">
            Start your first Lock
          </h2>
          <p className="mx-auto mt-3 max-w-md text-base leading-relaxed text-muted-foreground">
            Create an account with your phone number, then start a Lock or join one with an invite code.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link href={routes.signup} className={buttonVariants({ size: "lg" })}>
              Create account
            </Link>
            <Link href={routes.login} className={buttonVariants({ variant: "outline", size: "lg" })}>
              I have an account
            </Link>
          </div>

          {siteRoutes.forBanks && (
            <a
              href={siteRoutes.forBanks}
              className="mt-8 inline-flex items-center gap-1 text-sm font-bold text-muted-foreground transition-colors hover:text-link"
            >
              Are you a bank? See Sura for banks
              <HugeiconsIcon icon={ArrowUpRight01Icon} size={16} strokeWidth={2.5} />
            </a>
          )}
        </div>
      </div>
    </section>
  )
}
