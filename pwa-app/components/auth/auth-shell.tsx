import type { ReactNode } from "react"
import Link from "next/link"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft01Icon } from "@hugeicons/core-free-icons"
import { routes } from "@/config/routes"
import { Logo } from "@/components/layout/logo"
import { ThemeToggle } from "@/components/layout/theme-toggle"

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="hero-glow flex min-h-dvh flex-1 flex-col">
      <header className="grid grid-cols-[1fr_auto_1fr] items-center px-4 pt-3 sm:px-8 sm:pt-6">
        <Link
          href={routes.home}
          aria-label="Back to home"
          title="Back to home"
          className="inline-flex items-center gap-1 justify-self-start rounded-full p-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link sm:px-3"
        >
          <HugeiconsIcon icon={ArrowLeft01Icon} size={20} strokeWidth={2.5} />
          <span className="hidden sm:inline">Home</span>
        </Link>
        <Logo />
        <ThemeToggle className="justify-self-end" />
      </header>
      <main className="flex flex-1 items-start justify-center px-5 pt-6 pb-[max(2rem,env(safe-area-inset-bottom))] sm:items-center sm:px-8 sm:pt-10 sm:pb-12">
        {children}
      </main>
    </div>
  )
}
