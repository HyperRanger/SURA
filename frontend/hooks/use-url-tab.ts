"use client"

import { useState } from "react"
import { usePathname, useRouter } from "next/navigation"

// the open tab of a detail screen, mirrored into ?tab= so a refresh or a shared
// link lands on the same view. replace, not push, so back leaves the page
export function useUrlTab<T extends string>(initial: T) {
  const router = useRouter()
  const pathname = usePathname()
  const [tab, setTab] = useState<T>(initial)

  function go(next: T) {
    setTab(next)
    router.replace(`${pathname}?${new URLSearchParams({ tab: next })}`, { scroll: false })
  }

  return [tab, go] as const
}
