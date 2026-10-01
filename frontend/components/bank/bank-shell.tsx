"use client"

import { useEffect, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { HugeiconsIcon } from "@hugeicons/react"
import { Logout01Icon } from "@hugeicons/core-free-icons"
import { bankNav } from "@/config/bank"
import { routes } from "@/config/routes"
import { useHydrated } from "@/hooks/use-hydrated"
import { useStoredValue } from "@/hooks/use-stored-value"
import { endSession, sessionStore } from "@/lib/session"
import { Logo } from "@/components/layout/logo"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { humanize } from "@/utils/format"
import { isBankRole, withNext } from "@/utils/redirect"

function isActive(pathname: string, href: string) {
  return href === routes.bank.home ? pathname === href : pathname === href || pathname.startsWith(`${href}/`)
}

// the bank console frame. only bank staff sessions get past it; anyone else is
// sent to B1 with ?next= so they land back here after signing in
export function BankShell({ children }: { children: ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const hydrated = useHydrated()
  const session = useStoredValue(sessionStore)
  const allowed = session !== null && isBankRole(session.role)

  useEffect(() => {
    if (hydrated && !allowed) router.replace(withNext(routes.bank.login, pathname))
  }, [hydrated, allowed, pathname, router])

  if (!allowed) {
    return (
      <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
        <Spinner className="size-6" />
        <span className="sr-only">checking your bank session</span>
      </div>
    )
  }

  function handleSignOut() {
    endSession()
    router.replace(routes.bank.login)
  }

  return (
    <div className="flex min-h-dvh flex-1 flex-col lg:flex-row">
      <aside className="border-b-2 border-hairline bg-card lg:sticky lg:top-0 lg:flex lg:h-dvh lg:w-64 lg:shrink-0 lg:flex-col lg:border-r-2 lg:border-b-0">
        <div className="flex items-center justify-between gap-3 px-4 pt-4 pb-3 lg:px-5 lg:pt-6 lg:pb-6">
          <div className="flex items-center gap-2.5">
            <Logo />
            <span className="rounded-full bg-gold-soft px-2.5 py-0.5 text-[11px] font-extrabold text-gold-deep">bank</span>
          </div>
          <button
            type="button"
            onClick={handleSignOut}
            className="inline-flex items-center gap-1.5 rounded-full p-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link lg:hidden"
          >
            <HugeiconsIcon icon={Logout01Icon} size={18} strokeWidth={2.2} />
            <span className="sr-only">sign out</span>
          </button>
        </div>

        <nav aria-label="bank console" className="lg:flex-1 lg:overflow-y-auto">
          <ul className="flex gap-1.5 overflow-x-auto px-4 pb-3 lg:flex-col lg:gap-1 lg:px-3 lg:pb-0">
            {bankNav.map((item) => {
              const active = isActive(pathname, item.href)
              return (
                <li key={item.id} className="shrink-0">
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-full px-3.5 py-2 text-sm font-extrabold whitespace-nowrap transition-colors lg:rounded-2xl lg:px-3 lg:py-2.5",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-cloud hover:text-link"
                    )}
                  >
                    <HugeiconsIcon icon={item.icon} size={18} strokeWidth={2.2} className="hidden lg:block" />
                    {item.label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="hidden border-t-2 border-hairline p-4 lg:block">
          <p className="text-xs font-extrabold text-muted-foreground">signed in as</p>
          <p className="mt-0.5 truncate text-sm font-black">{humanize(session.role)}</p>
          {session.institutionId && (
            <p className="truncate font-mono text-xs font-semibold text-muted-foreground normal-case">
              {session.institutionId}
            </p>
          )}
          <button
            type="button"
            onClick={handleSignOut}
            className="mt-3 inline-flex items-center gap-1.5 rounded-full py-1.5 pr-3 pl-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
          >
            <HugeiconsIcon icon={Logout01Icon} size={18} strokeWidth={2.2} />
            sign out
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 pt-6 pb-16 sm:px-8 sm:pt-10">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>
    </div>
  )
}
