import type { ComponentProps } from "react"
import { cn } from "@/lib/utils"

type InputProps = ComponentProps<"input"> & {
  invalid?: boolean
}

// normal-case undoes the site-wide lowercase, so people see exactly what they type
export function Input({ className, invalid, ...props }: InputProps) {
  return (
    <input
      data-slot="input"
      aria-invalid={invalid || undefined}
      className={cn(
        "h-13 w-full rounded-2xl border-2 border-b-4 border-hairline bg-card px-4 text-base font-semibold normal-case transition-colors outline-none placeholder:font-normal placeholder:text-muted-foreground/70 placeholder:lowercase",
        "hover:border-hairline-strong focus-visible:border-primary focus-visible:ring-4 focus-visible:ring-ring/15",
        "disabled:cursor-not-allowed disabled:opacity-60",
        "aria-invalid:border-destructive aria-invalid:focus-visible:ring-destructive/15",
        className
      )}
      {...props}
    />
  )
}
