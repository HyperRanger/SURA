import { HugeiconsIcon } from "@hugeicons/react"
import type { ChoiceOption } from "@/types"
import { cn } from "@/lib/utils"

type ChoiceCardsProps<T extends string> = {
  name: string
  options: readonly ChoiceOption<T>[]
  value: T | ""
  onChange: (value: T) => void
  labelledBy?: string
  describedBy?: string
  invalid?: boolean
  columns?: 1 | 2
  className?: string
}

// a radio group drawn as tappable cards. native radios underneath keep arrow-key
// navigation and form semantics for free
export function ChoiceCards<T extends string>({
  name,
  options,
  value,
  onChange,
  labelledBy,
  describedBy,
  invalid,
  columns = 2,
  className,
}: ChoiceCardsProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      aria-invalid={invalid || undefined}
      className={cn("grid gap-3", columns === 2 && "grid-cols-2", className)}
    >
      {options.map((option) => {
        const id = `${name}-${option.value}`
        const selected = value === option.value

        return (
          <label
            key={option.value}
            htmlFor={id}
            className={cn(
              "relative flex cursor-pointer flex-col gap-2 rounded-2xl border-2 border-b-4 bg-card p-4 transition-colors",
              "has-focus-visible:ring-4 has-focus-visible:ring-ring/20",
              selected
                ? "border-primary bg-indigo-soft"
                : "border-hairline hover:border-hairline-strong",
              invalid && !selected && "border-destructive/50"
            )}
          >
            <input
              id={id}
              type="radio"
              name={name}
              value={option.value}
              checked={selected}
              onChange={() => onChange(option.value)}
              className="sr-only"
            />
            {option.icon && (
              <HugeiconsIcon
                icon={option.icon}
                size={22}
                strokeWidth={2}
                className={selected ? "text-link" : "text-muted-foreground"}
              />
            )}
            <span className="text-sm font-extrabold text-foreground">{option.label}</span>
            {option.description && (
              <span className="text-xs leading-snug font-semibold text-muted-foreground">
                {option.description}
              </span>
            )}
          </label>
        )
      })}
    </div>
  )
}
