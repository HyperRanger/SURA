"use client"

import { useRef, type ClipboardEvent, type KeyboardEvent } from "react"
import { cn } from "@/lib/utils"

type OtpInputProps = {
  value: string
  onChange: (value: string) => void
  // fires once every box is filled, with the full code
  onComplete?: (code: string) => void
  length?: number
  disabled?: boolean
  invalid?: boolean
  autoFocus?: boolean
  describedBy?: string
  label?: string
}

const onlyDigits = (text: string) => text.replace(/\D/g, "")

// one box per digit. typing moves forward, backspace moves back, and pasting or
// sms autofill drops the whole code in at once
export function OtpInput({
  value,
  onChange,
  onComplete,
  length = 6,
  disabled,
  invalid,
  autoFocus,
  describedBy,
  label = "Verification code",
}: OtpInputProps) {
  const refs = useRef<(HTMLInputElement | null)[]>([])
  const digits = Array.from({ length }, (_, i) => value[i] ?? "")

  const focusBox = (index: number) => {
    const box = refs.current[Math.max(0, Math.min(length - 1, index))]
    box?.focus()
    box?.select()
  }

  // the value never has gaps: typing past the end lands in the first empty box
  const fillFrom = (index: number, incoming: string) => {
    const chars = onlyDigits(incoming)
    if (!chars) return
    const start = Math.min(index, value.length)
    const code = (value.slice(0, start) + chars + value.slice(start + chars.length)).slice(0, length)

    onChange(code)
    focusBox(start + chars.length)
    if (code.length === length) onComplete?.(code)
  }

  // removes one digit and closes the gap, like deleting in a text field
  const removeAt = (index: number) => {
    onChange(value.slice(0, index) + value.slice(index + 1))
    focusBox(index)
  }

  const handleChange = (index: number, typed: string) => {
    const incoming = onlyDigits(typed)
    const current = digits[index]
    // if the old digit was not selected, the box holds old + new; keep only the new one
    const fresh =
      current && incoming.length === 2 ? (incoming[0] === current ? incoming[1] : incoming[0]) : incoming
    fillFrom(index, fresh)
  }

  const handleKeyDown = (index: number) => (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace") {
      event.preventDefault()
      if (digits[index]) removeAt(index)
      else if (index > 0) removeAt(index - 1)
    } else if (event.key === "ArrowLeft") {
      event.preventDefault()
      focusBox(index - 1)
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      focusBox(index + 1)
    }
  }

  const handlePaste = (index: number) => (event: ClipboardEvent<HTMLInputElement>) => {
    event.preventDefault()
    fillFrom(index, event.clipboardData.getData("text"))
  }

  return (
    <div role="group" aria-label={label} aria-describedby={describedBy} className="flex justify-between gap-2">
      {digits.map((digit, index) => (
        <input
          key={index}
          ref={(el) => {
            refs.current[index] = el
          }}
          value={digit}
          onChange={(event) => handleChange(index, event.target.value)}
          onKeyDown={handleKeyDown(index)}
          onPaste={handlePaste(index)}
          onFocus={(event) => event.target.select()}
          inputMode="numeric"
          autoComplete={index === 0 ? "one-time-code" : "off"}
          autoFocus={autoFocus && index === 0}
          disabled={disabled}
          aria-label={`Digit ${index + 1} of ${length}`}
          aria-invalid={invalid || undefined}
          className={cn(
            "h-14 w-full min-w-0 rounded-2xl border-2 border-b-4 border-hairline bg-card text-center text-2xl font-black text-foreground transition-colors outline-none sm:h-16",
            "focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/15",
            digit && "border-ring/40",
            invalid && "border-destructive",
            "disabled:opacity-60"
          )}
        />
      ))}
    </div>
  )
}
