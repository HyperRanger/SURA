"use client"

import { siteConfig } from "@/config/site"
import { useApiStatus } from "@/hooks/use-api-status"
import { cn } from "@/lib/utils"

const labels = {
  checking: "checking api",
  online: "api operational",
  offline: "api unreachable",
} as const

export function ApiStatus() {
  const enabled = Boolean(siteConfig.apiUrl)
  const status = useApiStatus(enabled)

  if (!enabled) return null

  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden="true"
        className={cn(
          "size-2 rounded-full",
          status === "online" && "bg-green",
          status === "offline" && "bg-orange",
          status === "checking" && "animate-pulse bg-hairline-strong"
        )}
      />
      {labels[status]}
    </span>
  )
}
