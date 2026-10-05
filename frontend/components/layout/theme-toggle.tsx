"use client"

import { useTheme } from "next-themes"
import { HugeiconsIcon } from "@hugeicons/react"
import { Moon02Icon, Sun03Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

// both icons are rendered and css picks one, so the server markup matches the
// client no matter which theme the visitor lands on
export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <button
      type="button"
      aria-label="toggle dark mode"
      title="toggle dark mode"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className={cn(
        "flex size-10 shrink-0 items-center justify-center rounded-full border-2 border-hairline text-foreground transition-colors hover:border-link hover:text-link",
        className
      )}
    >
      <HugeiconsIcon icon={Moon02Icon} size={18} strokeWidth={2} className="dark:hidden" />
      <HugeiconsIcon icon={Sun03Icon} size={18} strokeWidth={2} className="hidden dark:block" />
    </button>
  )
}
