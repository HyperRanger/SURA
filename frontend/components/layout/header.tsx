"use client"

import { mainNav } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import { MobileNav } from "@/components/layout/mobile-nav"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { useScrolled } from "@/hooks/use-scrolled"
import { cn } from "@/lib/utils"

export function Header() {
  const scrolled = useScrolled()

  return (
    <header
      className={cn(
        "sticky top-0 z-50 border-b transition-all duration-300",
        scrolled
          ? "border-hairline bg-background/90 backdrop-blur-md"
          : "border-transparent bg-background/60 backdrop-blur-sm"
      )}
    >
      <nav
        aria-label="primary"
        className="container-page flex h-18 items-center justify-between"
      >
        <Logo />

        <ul className="hidden items-center gap-8 lg:flex">
          {mainNav.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="text-sm font-bold text-muted-foreground transition-colors hover:text-link"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 lg:flex">
          <ThemeToggle />
          <a href="#how-it-works" className={buttonVariants({ variant: "outline", size: "sm" })}>
            see how it works
          </a>
          <a href="#get-started" className={buttonVariants({ size: "sm" })}>
            partner with us
          </a>
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          <ThemeToggle />
          <MobileNav />
        </div>
      </nav>
    </header>
  )
}
