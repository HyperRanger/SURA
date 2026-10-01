"use client"

import { useRef, type PointerEvent } from "react"
import { mainNav } from "@/config/site"
import { buttonVariants } from "@/components/ui/button"
import { Logo } from "@/components/layout/logo"
import { MobileNav } from "@/components/layout/mobile-nav"
import { useScrolled } from "@/hooks/use-scrolled"
import { cn } from "@/lib/utils"

export function Header() {
  const scrolled = useScrolled()
  const glassRef = useRef<HTMLElement>(null)

  // move the glare with the pointer, like light catching a pane of glass
  function handlePointerMove(event: PointerEvent<HTMLElement>) {
    const el = glassRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty("--glass-x", `${event.clientX - rect.left}px`)
    el.style.setProperty("--glass-y", `${event.clientY - rect.top}px`)
  }

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-[padding] duration-300",
        scrolled ? "pt-3" : "pt-4"
      )}
    >
      <div className="container-page">
        <nav
          ref={glassRef}
          onPointerMove={handlePointerMove}
          aria-label="primary"
          className="glass flex h-16 items-center justify-between rounded-full pr-3 pl-5"
        >
          <div className="flex items-center gap-8">
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
          </div>

          <div className="hidden items-center gap-3 lg:flex">
            <a href="#how-it-works" className={buttonVariants({ variant: "outline", size: "sm" })}>
              see how it works
            </a>
            <a href="#get-started" className={buttonVariants({ size: "sm" })}>
              partner with us
            </a>
          </div>

          <div className="flex items-center gap-2 lg:hidden">
            <MobileNav />
          </div>
        </nav>
      </div>
    </header>
  )
}
