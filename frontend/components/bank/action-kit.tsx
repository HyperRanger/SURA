"use client"

import { useEffect, useState, type ReactNode } from "react"
import type { ApiError } from "@/lib/api-error"
import { CopyButton } from "@/components/shared/copy-button"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

// a failed write, read the way the bank portal contract asks: 403 is a missing
// permission and is never retried, 409 means the record moved on underneath us
export function ActionError({ error, className }: { error: ApiError | null; className?: string }) {
  if (!error || error.kind === "cancelled") return null
  if (error.is(403)) {
    return (
      <Alert variant="info" title="your role can't do this" className={className}>
        ask a bank administrator to grant the permission to your account.
      </Alert>
    )
  }
  if (error.is(409)) {
    return (
      <Alert variant="error" title="this changed since you opened it" className={className}>
        {error.message} refresh to see the current state.
      </Alert>
    )
  }
  return (
    <Alert variant="error" className={className}>
      {error.message}
    </Alert>
  )
}

type ConfirmButtonProps = {
  children: ReactNode
  // what the button says once armed, e.g. "yes, revoke"
  confirmLabel: ReactNode
  onConfirm: () => void
  loading?: boolean
  disabled?: boolean
  variant?: "outline" | "default" | "ghost"
}

// a destructive action takes two taps: the first arms it, the second sends it.
// it disarms itself after a few seconds so a stray tap later does nothing
export function ConfirmButton({
  children,
  confirmLabel,
  onConfirm,
  loading,
  disabled,
  variant = "outline",
}: ConfirmButtonProps) {
  const [armed, setArmed] = useState(false)

  useEffect(() => {
    if (!armed) return
    const timer = setTimeout(() => setArmed(false), 4000)
    return () => clearTimeout(timer)
  }, [armed])

  return (
    <Button
      type="button"
      size="sm"
      variant={armed ? "default" : variant}
      loading={loading}
      disabled={disabled}
      className={armed ? "bg-destructive hover:bg-destructive/90 border-destructive" : undefined}
      onClick={() => {
        if (!armed) return setArmed(true)
        setArmed(false)
        onConfirm()
      }}
    >
      {armed ? confirmLabel : children}
    </Button>
  )
}

type SecretRevealProps = {
  title: string
  secret: string
  onDismiss: () => void
  children?: ReactNode
}

// a secret the api returns once. it lives only in component state, so leaving
// the page or dismissing it is the last time anyone can read it
export function SecretReveal({ title, secret, onDismiss, children }: SecretRevealProps) {
  return (
    <Alert
      variant="gold"
      title={title}
      action={
        <Button type="button" variant="outline" size="sm" onClick={onDismiss}>
          i&apos;ve stored it
        </Button>
      }
    >
      <p>copy it now. sura keeps only a hash and will never show it again.</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <code className="min-w-0 flex-1 rounded-xl bg-card px-3 py-2 font-mono text-xs break-all text-foreground normal-case">
          {secret}
        </code>
        <CopyButton value={secret} />
      </div>
      {children}
    </Alert>
  )
}
