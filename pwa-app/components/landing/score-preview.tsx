import { HugeiconsIcon } from "@hugeicons/react"
import { SquareLock01Icon } from "@hugeicons/core-free-icons"
import { scorePreview } from "@/config/landing"
import { Badge } from "@/components/ui/badge"

// an illustrative score: a half-dial for the total, then the five pillars with
// their weights. not anyone's real score
export function ScorePreview() {
  const { total, max, tier, pillars } = scorePreview
  const filled = (total / max) * 100

  return (
    <div aria-hidden="true" className="card-raised mx-auto w-full max-w-sm rounded-[2rem] p-5 select-none sm:p-6">
      <div className="flex items-center justify-between">
        <p className="text-sm font-bold">Your Sura Score</p>
        <span className="flex items-center gap-1 text-xs font-bold text-muted-foreground">
          <HugeiconsIcon icon={SquareLock01Icon} size={14} strokeWidth={2.2} />
          Only you
        </span>
      </div>

      <div className="relative mx-auto mt-4 w-full max-w-64">
        <svg viewBox="0 0 200 110" className="w-full">
          <defs>
            <linearGradient id="score-arc" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stopColor="var(--primary)" />
              <stop offset="100%" stopColor="var(--gold)" />
            </linearGradient>
          </defs>
          <path d="M 14 100 A 86 86 0 0 1 186 100" pathLength={100} fill="none" stroke="var(--cloud)" strokeWidth={16} strokeLinecap="round" />
          <path
            d="M 14 100 A 86 86 0 0 1 186 100"
            pathLength={100}
            fill="none"
            stroke="url(#score-arc)"
            strokeWidth={16}
            strokeLinecap="round"
            strokeDasharray={`${filled} 100`}
          />
        </svg>
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
          <p className="text-4xl leading-none font-bold tracking-tight tabular-nums">{total}</p>
          <p className="mt-1 text-xs font-bold text-muted-foreground">of {max}</p>
        </div>
      </div>

      <div className="mt-3 flex justify-center">
        <Badge variant="gold">{tier}</Badge>
      </div>

      <ul className="mt-5 flex flex-col gap-2.5">
        {pillars.map((pillar) => (
          <li key={pillar.label}>
            <div className="flex justify-between text-xs font-bold">
              <span>
                {pillar.label} <span className="text-muted-foreground">· {pillar.weight}%</span>
              </span>
              <span className="text-muted-foreground tabular-nums">
                {pillar.points}/{pillar.max}
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-cloud">
              <div className="h-full rounded-full bg-primary" style={{ width: `${(pillar.points / pillar.max) * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
