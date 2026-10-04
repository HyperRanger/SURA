import { MAX_SCORE, scorePillars } from "@/config/bank"
import type { ScoreReport } from "@/types"

// the five pillar bars. each bar fills toward that pillar's share of 1000, and the
// points always add up to the score, so nothing is hidden
export function ScorePillars({ report }: { report: ScoreReport }) {
  return (
    <ul className="flex flex-col gap-4">
      {scorePillars.map((pillar) => {
        const max = Math.round((report.weights?.[pillar.key] ?? pillar.weight) * MAX_SCORE)
        const points = report.breakdown[pillar.key] ?? 0
        const fill = max > 0 ? Math.min(100, (points / max) * 100) : 0

        return (
          <li key={pillar.key}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-extrabold">{pillar.label}</span>
              <span className="shrink-0 font-bold tabular-nums text-muted-foreground">
                <span className="text-foreground">{points}</span> / {max}
              </span>
            </div>
            <div
              role="meter"
              aria-label={pillar.label}
              aria-valuemin={0}
              aria-valuemax={max}
              aria-valuenow={points}
              className="mt-1.5 h-3 overflow-hidden rounded-full bg-cloud"
            >
              <div className="h-full rounded-full bg-ring transition-[width]" style={{ width: `${fill}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

// the headline number. gold is reserved for scores, as the brand rules ask
export function ScoreFigure({ report }: { report: ScoreReport }) {
  return (
    <div className="flex items-end gap-2">
      <span className="text-5xl font-black tracking-tight text-gold-deep tabular-nums">{report.score}</span>
      <span className="pb-1.5 text-sm font-extrabold text-muted-foreground">/ {MAX_SCORE}</span>
    </div>
  )
}
