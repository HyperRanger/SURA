"use client"

import { useEffect, useState } from "react"
import { getApiHealth } from "@/actions/health"
import type { ApiStatus } from "@/types"

export function useApiStatus(enabled: boolean) {
  const [status, setStatus] = useState<ApiStatus>("checking")

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    getApiHealth().then((ok) => {
      if (!cancelled) setStatus(ok ? "online" : "offline")
    })
    return () => {
      cancelled = true
    }
  }, [enabled])

  return status
}
