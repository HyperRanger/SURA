"use client"

import { useEffect, useState, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { HugeiconsIcon } from "@hugeicons/react"
import { Logout01Icon, Menu01Icon } from "@hugeicons/core-free-icons"
import { bankNav } from "@/config/bank"
import { routes } from "@/config/routes"
import { useHydrated } from "@/hooks/use-hydrated"
import { useStoredValue } from "@/hooks/use-stored-value"
import { endSession, sessionStore } from "@/lib/session"
import { Logo } from "@/components/layout/logo"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import type { Session } from "@/types"
import { humanize } from "@/utils/format"
import { isBankRole, withNext } from "@/utils/redirect"

function isActive(pathname: string, href: string) {
  return href === routes.bank.home ? pathname === href : pathname === href || pathname.startsWith(`${href}/`)
}

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
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b-2 border-hairline bg-card px-4 py-3 lg:hidden">
        <BankBrand />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <MobileMenu pathname={pathname} session={session} onSignOut={handleSignOut} />
        </div>
      </header>

      <aside className="hidden border-r-2 border-hairline bg-card lg:sticky lg:top-0 lg:flex lg:h-dvh lg:w-64 lg:shrink-0 lg:flex-col">
        <div className="flex items-center justify-between gap-3 px-5 pt-6 pb-6">
          <BankBrand />
          <ThemeToggle />
        </div>
        <nav aria-label="bank console" className="flex-1 overflow-y-auto px-3">
          <NavLinks pathname={pathname} />
        </nav>
        <div className="border-t-2 border-hairline p-4">
          <AccountSummary session={session} onSignOut={handleSignOut} />
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 pt-6 pb-16 sm:px-8 sm:pt-10">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>
    </div>
  )
}

function BankBrand() {
  return (
    <div className="flex items-center gap-2.5">
      <Logo />
    </div>
  )
}

function NavLinks({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <ul className="flex flex-col gap-1">
      {bankNav.map((item) => {
        const active = isActive(pathname, item.href)
        return (
          <li key={item.id}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-extrabold transition-colors",
                active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-cloud hover:text-link"
              )}
            >
              <HugeiconsIcon icon={item.icon} size={18} strokeWidth={2.2} />
              {item.label}
            </Link>
          </li>
        )
      })}
    </ul>
  )
}

function AccountSummary({ session, onSignOut }: { session: Session; onSignOut: () => void }) {
  return (
    <>
      <p className="text-xs font-extrabold text-muted-foreground">signed in as</p>
      <p className="mt-0.5 truncate text-sm font-black">{humanize(session.role)}</p>
      {session.institutionId && (
        <p className="truncate font-mono text-xs font-semibold text-muted-foreground normal-case">
          {session.institutionId}
        </p>
      )}
      <button
        type="button"
        onClick={onSignOut}
        className="mt-3 inline-flex items-center gap-1.5 rounded-full py-1.5 pr-3 pl-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
      >
        <HugeiconsIcon icon={Logout01Icon} size={18} strokeWidth={2.2} />
        sign out
      </button>
    </>
  )
}

type MobileMenuProps = {
  pathname: string
  session: Session
  onSignOut: () => void
}

function MobileMenu({ pathname, session, onSignOut }: MobileMenuProps) {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  const current = bankNav.find((item) => isActive(pathname, item.href))

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="open console menu"
        className="flex h-10 items-center gap-2 rounded-full border-2 border-hairline pr-2.5 pl-3.5 text-sm font-extrabold text-foreground transition-colors hover:border-link hover:text-link"
      >
        {current?.label ?? "menu"}
        <HugeiconsIcon icon={Menu01Icon} size={20} strokeWidth={2} />
      </SheetTrigger>

      <SheetContent side="right" className="w-full max-w-xs gap-0 lowercase">
        <SheetHeader className="p-5">
          <SheetTitle render={<div />}>
            <BankBrand />
          </SheetTitle>
          <SheetDescription className="sr-only">bank console navigation</SheetDescription>
        </SheetHeader>

        <nav aria-label="bank console" className="flex-1 overflow-y-auto px-3">
          <NavLinks pathname={pathname} onNavigate={close} />
        </nav>

        <div className="border-t-2 border-hairline p-5">
          <AccountSummary session={session} onSignOut={onSignOut} />
        </div>
      </SheetContent>
    </Sheet>
  )
}
