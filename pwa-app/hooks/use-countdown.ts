"use client"

import { useEffect, useState } from "react"

// whole seconds left until a timestamp (ms), ticking once a second and stopping at zero
export function useCountdown(targetMs: number) {
  const [now, setNow] = useState(() => Date.now())
  const secondsLeft = Math.max(0, Math.ceil((targetMs - now) / 1000))

  useEffect(() => {
    if (secondsLeft <= 0) return
    const id = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [secondsLeft, targetMs])

  return secondsLeft
}
