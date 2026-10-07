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
        Didn&apos;t get it? You can resend in{" "}
        <span className="font-bold text-foreground tabular-nums">{formatCountdown(secondsLeft)}</span>
      </p>
    )
  }

  return (
    <p className="text-sm font-semibold text-muted-foreground">
      Didn&apos;t get it?{" "}
      <Button type="button" variant="link" size="sm" loading={loading} onClick={onResend} className="h-auto px-0">
        Resend code
      </Button>
    </p>
  )
}
