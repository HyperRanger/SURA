"use client"

import { useCountdown } from "@/hooks/use-countdown"
import { Button } from "@/components/ui/button"
import { formatCountdown } from "@/utils/format"

type ResendCodeProps = {
  availableAt: number
  onResend: () => void
  loading?: boolean
}

// remount with key={availableAt} after a resend so the countdown starts fresh
export function ResendCode({ availableAt, onResend, loading }: ResendCodeProps) {
  const secondsLeft = useCountdown(availableAt)

  if (secondsLeft > 0) {
    return (
      <p className="text-sm font-semibold text-muted-foreground" aria-live="polite">
        didn&apos;t get it? you can resend in{" "}
        <span className="font-extrabold text-foreground tabular-nums">{formatCountdown(secondsLeft)}</span>
      </p>
    )
  }

  return (
    <p className="text-sm font-semibold text-muted-foreground">
      didn&apos;t get it?{" "}
      <Button type="button" variant="link" size="sm" loading={loading} onClick={onResend} className="h-auto px-0">
        resend code
      </Button>
    </p>
  )
}
