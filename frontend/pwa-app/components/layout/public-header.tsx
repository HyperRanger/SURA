"use client"

import Link from "next/link"
import { routes } from "@/config/routes"
import { landingNav } from "@/config/site"
import { useScrolled } from "@/hooks/use-scrolled"
import { useStoredValue } from "@/hooks/use-stored-value"
import { sessionStore } from "@/lib/session"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { homeForRole } from "@/utils/redirect"

// a slim app bar on phones; the landing anchors join it on wider screens.
// someone already signed in gets a way straight back into the app
export function PublicHeader() {
  const scrolled = useScrolled()
  const session = useStoredValue(sessionStore)

  return (
    <header className={cn("sticky top-0 z-50 transition-[padding] duration-300", scrolled ? "pt-2" : "pt-3")}>
      <div className="container-app">
        <nav aria-label="Primary" className="glass flex h-14 items-center justify-between rounded-full pr-2 pl-4">
          <div className="flex items-center gap-8">
            <Logo />
            <ul className="hidden items-center gap-7 md:flex">
              {landingNav.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-sm font-bold text-muted-foreground transition-colors hover:text-link">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {session ? (
              <Link href={homeForRole(session.role)} className={buttonVariants({ size: "sm" })}>
                Open Sura
              </Link>
            ) : (
              <>
                <Link href={routes.login} className={buttonVariants({ variant: "ghost", size: "sm", className: "max-sm:px-3" })}>
                  Log in
                </Link>
                <Link href={routes.signup} className={buttonVariants({ size: "sm", className: "hidden sm:inline-flex" })}>
                  Get started
                </Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  )
}
