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
  className?: string
}

// a radio group drawn as full-width rows: icon, text, then a radio dot. native
// radios underneath keep arrow-key navigation and form semantics for free
export function ChoiceCards<T extends string>({
  name,
  options,
  value,
  onChange,
  labelledBy,
  describedBy,
  invalid,
  className,
}: ChoiceCardsProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-labelledby={labelledBy}
      aria-describedby={describedBy}
      aria-invalid={invalid || undefined}
      className={cn("flex flex-col gap-3", className)}
    >
      {options.map((option) => {
        const id = `${name}-${option.value}`
        const selected = value === option.value

        return (
          <label
            key={option.value}
            htmlFor={id}
            className={cn(
              "flex cursor-pointer items-center gap-4 rounded-2xl border-2 border-b-4 bg-card px-4 py-3.5 transition-colors",
              "has-focus-visible:ring-4 has-focus-visible:ring-ring/20",
              selected
                ? "border-ring bg-indigo-soft"
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
              <span
                className={cn(
                  "flex size-11 shrink-0 items-center justify-center rounded-full transition-colors",
                  selected ? "bg-primary text-primary-foreground" : "bg-cloud text-muted-foreground"
                )}
              >
                <HugeiconsIcon icon={option.icon} size={22} strokeWidth={2} />
              </span>
            )}
            <span className="min-w-0 flex-1">
              <span className="block text-[15px] font-bold text-foreground">{option.label}</span>
              {option.description && (
                <span className="block text-xs leading-snug font-semibold text-muted-foreground">
                  {option.description}
                </span>
              )}
            </span>
            <span
              aria-hidden="true"
              className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                selected ? "border-ring" : "border-hairline-strong"
              )}
            >
              <span
                className={cn(
                  "size-3 rounded-full bg-ring transition-transform",
                  selected ? "scale-100" : "scale-0"
                )}
              />
            </span>
          </label>
        )
      })}
    </div>
  )
}
