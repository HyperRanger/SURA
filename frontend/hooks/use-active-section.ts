"use client"

import { useEffect, useState } from "react"

// tracks which section the reader is in: the last one whose top has passed the offset line
export function useActiveSection(ids: string[], offset = 140) {
  const [active, setActive] = useState(ids[0])

  useEffect(() => {
    const onScroll = () => {
      // at the very bottom the last sections may never reach the line, so pick the last one
      const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2
      if (atBottom) {
        setActive(ids[ids.length - 1])
        return
      }

      let current = ids[0]
      for (const id of ids) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top - offset <= 0) current = id
      }
      setActive(current)
    }

    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
    }
  }, [ids, offset])

  return active
}
