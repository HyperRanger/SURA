"use client"

import { HugeiconsIcon } from "@hugeicons/react"
import { Moon02Icon, Sun03Icon } from "@hugeicons/core-free-icons"
import { useTheme } from "next-themes"
import { cn } from "@/lib/utils"

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme()
  const isDark = resolvedTheme === "dark"

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "switch to light mode" : "switch to dark mode"}
      className={cn(
        "flex size-10 items-center justify-center rounded-full border-2 border-hairline text-muted-foreground transition-colors hover:border-link hover:text-link",
        className
      )}
    >
      {/* both icons render so server and client markup match; css picks one */}
      <HugeiconsIcon icon={Moon02Icon} size={18} strokeWidth={2} className="dark:hidden" />
      <HugeiconsIcon icon={Sun03Icon} size={18} strokeWidth={2} className="hidden dark:block" />
    </button>
  )
}
