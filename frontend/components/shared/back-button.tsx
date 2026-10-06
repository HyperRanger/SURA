"use client"

import { useRouter } from "next/navigation"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft01Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

type BackButtonProps = {
  // used when there is no history to go back to, e.g. the page was opened from a link
  fallbackHref: string
  label?: string
  className?: string
}

export function BackButton({ fallbackHref, label = "Back", className }: BackButtonProps) {
  const router = useRouter()

  function handleClick() {
    if (window.history.length > 1) router.back()
    else router.push(fallbackHref)
  }

  return (
    <button
      type="button"
      title={label === "Back" ? "Go back" : `Back to ${label.toLowerCase()}`}
      onClick={handleClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-full py-2 pr-3 pl-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link",
        className
      )}
    >
      <HugeiconsIcon icon={ArrowLeft01Icon} size={18} strokeWidth={2.5} />
      {label}
    </button>
  )
}
