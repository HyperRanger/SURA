import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

// ids for wiring a control to its hint and error, so screen readers read both
export function fieldIds(id: string) {
  return { hint: `${id}-hint`, error: `${id}-error` }
}

export function describedBy(id: string, { hint, error }: { hint?: ReactNode; error?: string }) {
  const ids = fieldIds(id)
  const parts = [hint ? ids.hint : null, error ? ids.error : null].filter(Boolean)
  return parts.length ? parts.join(" ") : undefined
}

type FieldProps = {
  id: string
  label: ReactNode
  hint?: ReactNode
  error?: string
  // set false when the control is a group that labels itself, like a radio group
  asLabel?: boolean
  className?: string
  children: ReactNode
}

export function Field({ id, label, hint, error, asLabel = true, className, children }: FieldProps) {
  const ids = fieldIds(id)
  const LabelTag = asLabel ? "label" : "span"

  return (
    <div data-slot="field" className={cn("flex flex-col gap-2", className)}>
      <LabelTag
        {...(asLabel ? { htmlFor: id } : { id: `${id}-label` })}
        className="text-sm font-bold text-foreground"
      >
        {label}
      </LabelTag>
      {children}
      {hint && !error && (
        <p id={ids.hint} className="text-xs font-semibold text-muted-foreground">
          {hint}
        </p>
      )}
      <FieldError id={ids.error} message={error} />
    </div>
  )
}

export function FieldError({ id, message }: { id?: string; message?: string }) {
  if (!message) return null
  return (
    <p id={id} role="alert" className="text-xs font-bold text-destructive">
      {message}
    </p>
  )
}
