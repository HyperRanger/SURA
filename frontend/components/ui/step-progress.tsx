import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft01Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

type StepProgressProps = {
  // zero-based
  current: number
  total: number
  // hidden on the first step, where there is nowhere to go back to
  onBack?: () => void
  label?: string
  className?: string
}

// back button, "step 2 of 3" and a segmented bar. shared by every multi-step flow
export function StepProgress({ current, total, onBack, label = "progress", className }: StepProgressProps) {
  const canGoBack = Boolean(onBack) && current > 0

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="flex h-8 items-center justify-between">
        {canGoBack ? (
          <button
            type="button"
            onClick={onBack}
            className="-ml-2 inline-flex items-center gap-1 rounded-full py-1.5 pr-3 pl-2 text-sm font-bold text-muted-foreground transition-colors hover:bg-cloud hover:text-link"
          >
            <HugeiconsIcon icon={ArrowLeft01Icon} size={18} strokeWidth={2.5} />
            Back
          </button>
        ) : (
          <span />
        )}
        <span className="text-xs font-bold text-muted-foreground" aria-live="polite">
          Step {current + 1} of {total}
        </span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={1}
        aria-valuemax={total}
        aria-valuenow={current + 1}
        className="flex gap-1.5"
      >
        {Array.from({ length: total }, (_, index) => (
          <span
            key={index}
            className={cn(
              "h-2 flex-1 rounded-full transition-colors duration-300",
              index <= current ? "bg-ring" : "bg-hairline"
            )}
          />
        ))}
      </div>
    </div>
  )
}
