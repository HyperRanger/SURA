import { cn } from "@/lib/utils"

// "+44" in gold, "−44" in red, "0" muted. "new" for the first score on record
export function ScoreDelta({ before, after }: { before: number | null; after: number }) {
  if (before === null) return <span className="text-muted-foreground">New</span>
  const delta = after - before
  return (
    <span
      className={cn(
        "font-extrabold tabular-nums",
        delta > 0 && "text-gold-deep",
        delta < 0 && "text-destructive",
        delta === 0 && "text-muted-foreground"
      )}
    >
      {delta > 0 ? `+${delta}` : delta < 0 ? `−${Math.abs(delta)}` : "0"}
    </span>
  )
}
