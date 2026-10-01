"use client"

import { useEffect, useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle02Icon, Copy01Icon } from "@hugeicons/core-free-icons"
import { Button } from "@/components/ui/button"

// copies text and says so for a moment. stays quiet if the browser refuses
export function CopyButton({ value, label = "copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = setTimeout(() => setCopied(false), 2000)
    return () => clearTimeout(timer)
  }, [copied])

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
    } catch {
      // clipboard blocked, e.g. an insecure origin; the text is still selectable
    }
  }

  return (
    <Button type="button" variant="outline" size="sm" onClick={handleCopy} aria-live="polite">
      <HugeiconsIcon icon={copied ? CheckmarkCircle02Icon : Copy01Icon} size={18} strokeWidth={2.2} />
      {copied ? "copied" : label}
    </Button>
  )
}
