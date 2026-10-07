import type { ComponentProps, ReactNode } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { Tick02Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

type CheckboxProps = Omit<ComponentProps<"input">, "type"> & {
  label: ReactNode
  invalid?: boolean
}

// a native checkbox, visually replaced, so forms and keyboards behave as expected
export function Checkbox({ id, label, invalid, className, ...props }: CheckboxProps) {
  return (
    <label htmlFor={id} className={cn("flex cursor-pointer items-start gap-3", className)}>
      <span className="relative mt-0.5 flex size-6 shrink-0">
        <input
          id={id}
          type="checkbox"
          aria-invalid={invalid || undefined}
          className={cn(
            "peer size-6 cursor-pointer appearance-none rounded-lg border-2 border-b-[3px] border-hairline-strong bg-card transition-colors outline-none",
            "checked:border-primary-deep checked:bg-primary",
            "focus-visible:ring-4 focus-visible:ring-ring/20",
            "aria-invalid:border-destructive"
          )}
          {...props}
        />
        <HugeiconsIcon
          icon={Tick02Icon}
          size={16}
          strokeWidth={3}
          className="pointer-events-none absolute inset-0 m-auto text-primary-foreground opacity-0 peer-checked:opacity-100"
        />
      </span>
      <span className="text-sm leading-relaxed font-semibold text-muted-foreground">{label}</span>
    </label>
  )
}
