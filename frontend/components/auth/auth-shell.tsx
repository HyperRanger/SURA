import type { ReactNode } from "react"
import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft01Icon, CheckmarkCircle02Icon } from "@hugeicons/core-free-icons"
import { routes } from "@/config/routes"
import { Logo } from "@/components/layout/logo"

const assurances = [
  "sura never holds your money",
  "payouts go to a vendor your group picks",
  "every score point is explained",
]

// mobile: logo bar and a single column. desktop: an indigo brand panel on the left
// that stays pinned to the viewport while the form side scrolls
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-1 lg:grid lg:grid-cols-[0.9fr_1.1fr]">
      <aside className="relative hidden overflow-hidden bg-primary p-12 text-primary-foreground lg:sticky lg:top-0 lg:flex lg:h-dvh lg:flex-col lg:self-start">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-24 -right-24 size-96 rounded-full bg-primary-bright/60 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-0 left-0 size-72 rounded-full bg-gold/20 blur-3xl"
        />
        <Logo tone="inverse" className="relative" />
        <div className="relative mt-auto max-w-md">
          <p className="text-4xl leading-tight font-black tracking-tight text-balance">
            save together. build a record <span className="text-gold">banks can read.</span>
          </p>
          <ul className="mt-8 flex flex-col gap-3">
            {assurances.map((item) => (
              <li key={item} className="flex items-center gap-3 text-sm font-bold text-primary-foreground/85">
                <HugeiconsIcon icon={CheckmarkCircle02Icon} size={20} strokeWidth={2} className="text-gold" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between px-5 pt-5 sm:px-8">
          <Logo className="lg:invisible" />
          <Link
            href={routes.home}
            className="inline-flex items-center gap-1 rounded-full px-3 py-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
          >
            <HugeiconsIcon icon={ArrowLeft01Icon} size={18} strokeWidth={2.5} />
            home
          </Link>
        </header>
        <main className="flex flex-1 items-start justify-center px-5 pt-8 pb-12 sm:items-center sm:px-8">
          <div className="w-full max-w-md">{children}</div>
        </main>
      </div>
    </div>
  )
}
