"use client"

import { useEffect, useState, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { HugeiconsIcon } from "@hugeicons/react"
import { Logout01Icon, Menu01Icon, UnfoldMoreIcon } from "@hugeicons/core-free-icons"
import { bankLogout } from "@/actions/bank"
import { bankNav, type BankNavItem } from "@/config/bank"
import { routes } from "@/config/routes"
import { canBank } from "@/hooks/use-bank-access"
import { useHydrated } from "@/hooks/use-hydrated"
import { useStoredValue } from "@/hooks/use-stored-value"
import { endSession, sessionStore } from "@/lib/session"
import { Alert } from "@/components/ui/alert"
import { Avatar, AvatarFallback, AvatarImage, dicebearUrl } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuLinkItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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

// only the sections this session can open, so nothing in the sidebar answers 403
function visibleNav(session: Session | null) {
  return bankNav.filter((item) => canBank(session, item.permission))
}

export function BankShell({ children }: { children: ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const hydrated = useHydrated()
  const session = useStoredValue(sessionStore)
  const allowed = session !== null && isBankRole(session.role)
  const nav = visibleNav(session)
  const section = bankNav.find((item) => isActive(pathname, item.href))
  const sectionAllowed = !section || canBank(session, section.permission)
  // a role without the overview, like an integration engineer, starts on its first section
  const landing = pathname === routes.bank.home && !sectionAllowed ? nav[0]?.href : undefined

  useEffect(() => {
    if (hydrated && !allowed) router.replace(withNext(routes.bank.login, pathname))
  }, [hydrated, allowed, pathname, router])

  useEffect(() => {
    if (landing) router.replace(landing)
  }, [landing, router])

  if (!allowed || landing) {
    return (
      <div className="flex flex-1 items-center justify-center py-20 text-muted-foreground">
        <Spinner className="size-6" />
        <span className="sr-only">Checking your bank session</span>
      </div>
    )
  }

  function handleSignOut() {
    // revoke server side too, but never keep someone signed in because the api is unreachable
    if (session) bankLogout(session.accessToken).catch(() => undefined)
    endSession()
    router.replace(routes.bank.login)
  }

  return (
    <div className="flex min-h-dvh flex-1 flex-col lg:flex-row">
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b-2 border-hairline bg-card px-4 py-3 lg:hidden">
        <BankBrand />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <MobileMenu nav={nav} pathname={pathname} session={session} onSignOut={handleSignOut} />
        </div>
      </header>

      <aside className="hidden border-r-2 border-hairline bg-card lg:sticky lg:top-0 lg:flex lg:h-dvh lg:w-64 lg:shrink-0 lg:flex-col">
        <div className="flex items-center justify-between gap-3 px-5 pt-6 pb-6">
          <BankBrand />
          <ThemeToggle />
        </div>
        <nav aria-label="Bank console" className="flex-1 overflow-y-auto px-3">
          <NavLinks nav={nav} pathname={pathname} />
        </nav>
        <div className="border-t-2 border-hairline p-4">
          <AccountMenu nav={nav} session={session} onSignOut={handleSignOut} />
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 pt-6 pb-16 sm:px-8 sm:pt-10">
        <div className="mx-auto w-full max-w-6xl">
          {sectionAllowed ? children : <NoAccess label={section?.label ?? "this section"} />}
        </div>
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

function NoAccess({ label }: { label: string }) {
  return (
    <Alert variant="info" title={`Your role can't open ${label.toLowerCase()}`}>
      Ask a bank administrator to grant this permission to your account.
    </Alert>
  )
}

type NavLinksProps = {
  nav: BankNavItem[]
  pathname: string
  onNavigate?: () => void
}

function NavLinks({ nav, pathname, onNavigate }: NavLinksProps) {
  return (
    <ul className="flex flex-col gap-1">
      {nav.map((item) => {
        const active = isActive(pathname, item.href)
        return (
          <li key={item.id}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-bold transition-colors",
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

// the account sections that live behind the avatar rather than in the main list
const accountSections = ["B14", "B12", "B13"]

function UserAvatar({ session, className }: { session: Session; className?: string }) {
  const initials = humanize(session.role)
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
  return (
    <Avatar className={className}>
      <AvatarImage src={dicebearUrl(session.userId)} alt="" />
      <AvatarFallback>{initials}</AvatarFallback>
    </Avatar>
  )
}

type AccountMenuProps = {
  nav: BankNavItem[]
  session: Session
  onSignOut: () => void
  onNavigate?: () => void
}

// everything about the signed-in person folds into one avatar; the menu opens upward
// from the foot of the sidebar with who they are, their own pages and sign out
function AccountMenu({ nav, session, onSignOut, onNavigate }: AccountMenuProps) {
  const role = humanize(session.role)
  const links = accountSections
    .map((id) => nav.find((item) => item.id === id))
    .filter((item): item is BankNavItem => Boolean(item))

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        title={`Signed in as ${role}. Open account menu`}
        className="group flex w-full cursor-pointer items-center gap-3 rounded-2xl border-2 border-transparent p-1.5 pr-2.5 text-left transition-colors outline-none hover:border-hairline hover:bg-cloud focus-visible:ring-4 focus-visible:ring-ring/30 data-popup-open:border-hairline data-popup-open:bg-cloud"
      >
        <UserAvatar session={session} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-bold">{role}</span>
          <span className="block text-xs font-bold text-muted-foreground">Your account</span>
        </span>
        <HugeiconsIcon
          icon={UnfoldMoreIcon}
          size={18}
          strokeWidth={2.2}
          className="shrink-0 text-muted-foreground transition-colors group-hover:text-link"
        />
      </DropdownMenuTrigger>

      <DropdownMenuContent side="top" align="start" className="w-(--anchor-width) min-w-60">
        <div className="mb-1 flex items-center gap-3 rounded-2xl bg-indigo-soft/60 p-3">
          <UserAvatar session={session} className="size-12 border-card" />
          <div className="min-w-0">
            <p className="truncate text-sm font-bold">{role}</p>
            {session.institutionId && (
              <p className="truncate font-mono text-xs font-semibold text-muted-foreground" title={session.institutionId}>
                {session.institutionId}
              </p>
            )}
          </div>
        </div>

        {links.length > 0 && (
          <DropdownMenuGroup>
            <DropdownMenuLabel>Manage</DropdownMenuLabel>
            {links.map((item) => (
              <DropdownMenuLinkItem
                key={item.id}
                title={`Open ${item.label.toLowerCase()}`}
                render={<Link href={item.href} onClick={onNavigate} />}
              >
                <HugeiconsIcon icon={item.icon} size={18} strokeWidth={2.2} />
                {item.id === "B14" ? "Your account" : item.label}
              </DropdownMenuLinkItem>
            ))}
          </DropdownMenuGroup>
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" title="Sign out of the bank console" onClick={onSignOut}>
          <HugeiconsIcon icon={Logout01Icon} size={18} strokeWidth={2.2} />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

type MobileMenuProps = {
  nav: BankNavItem[]
  pathname: string
  session: Session
  onSignOut: () => void
}

function MobileMenu({ nav, pathname, session, onSignOut }: MobileMenuProps) {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  const current = nav.find((item) => isActive(pathname, item.href))

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="Open console menu"
        title="Open console menu"
        className="flex h-10 items-center gap-2 rounded-full border-2 border-hairline pr-2.5 pl-3.5 text-sm font-bold text-foreground transition-colors hover:border-link hover:text-link"
      >
        {current?.label ?? "menu"}
        <HugeiconsIcon icon={Menu01Icon} size={20} strokeWidth={2} />
      </SheetTrigger>

      <SheetContent side="right" className="w-full max-w-xs gap-0">
        <SheetHeader className="p-5">
          <SheetTitle render={<div />}>
            <BankBrand />
          </SheetTitle>
          <SheetDescription className="sr-only">Bank console navigation</SheetDescription>
        </SheetHeader>

        <nav aria-label="Bank console" className="flex-1 overflow-y-auto px-3">
          <NavLinks nav={nav} pathname={pathname} onNavigate={close} />
        </nav>

        <div className="border-t-2 border-hairline p-5">
          <AccountMenu nav={nav} session={session} onSignOut={onSignOut} onNavigate={close} />
        </div>
      </SheetContent>
    </Sheet>
  )
}
