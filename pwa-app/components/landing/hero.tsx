import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowRight01Icon } from "@hugeicons/core-free-icons"
import { isDemoEnabled } from "@/config/env"
import { routes } from "@/config/routes"
import { buttonVariants } from "@/components/ui/button"
import { LockPreview } from "@/components/landing/lock-preview"

export function Hero() {
  return (
    <section className=" overflow-hidden pt-8 pb-16 md:pt-16 md:pb-24">
      <div className="container-app grid items-center gap-14 md:grid-cols-[1.05fr_0.95fr]">
        <div>
          <h1 className="mt-4 text-[2.5rem] leading-[1.05] font-bold tracking-tight text-balance sm:text-5xl md:text-6xl">
            Your ajo, with the <span className="text-link">rules built in.</span>
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
            Save with people you trust. Everyone pays on schedule, each payout goes straight to a shop you all agreed
            on, and every on-time contribution builds your Sura Score.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href={routes.signup} className={buttonVariants({ size: "lg" })}>
              Create account
              <HugeiconsIcon icon={ArrowRight01Icon} size={20} strokeWidth={2.5} />
            </Link>
            <Link href={routes.login} className={buttonVariants({ variant: "outline", size: "lg" })}>
              Log in
            </Link>
          </div>

          {isDemoEnabled && (
            <p className="mt-5 text-center text-sm font-semibold text-muted-foreground sm:text-left">
              Just looking?{" "}
              <Link href={routes.demo} className="font-bold text-link underline-offset-4 hover:underline">
                Try the demo
              </Link>
            </p>
          )}
        </div>

        <LockPreview />
      </div>
    </section>
  )
}
