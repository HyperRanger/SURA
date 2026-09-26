import { HugeiconsIcon } from "@hugeicons/react"
import { Store01Icon, Tick02Icon, Ticket01Icon } from "@hugeicons/core-free-icons"
import { circlePreview, scorePreview } from "@/config/landing"
import { formatNaira, initials } from "@/utils/format"
import { cn } from "@/lib/utils"

const avatarColors = ["bg-primary", "bg-orange", "bg-green", "bg-primary-deep", "bg-orange-deep"]

// an illustrative, static snapshot of a circle and a score, not live data
export function HeroPreview() {
  const { members, amount, cycle, cycles } = circlePreview
  const paidCount = members.filter((m) => m.paid).length
  const pot = amount * members.length
  const progress = Math.round((paidCount / members.length) * 100)

  return (
    <div className="relative mx-auto w-full max-w-md lg:max-w-none">
      <div className="card-raised rounded-[2rem] p-5 sm:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-extrabold tracking-wide text-muted-foreground">
              rotating circle · {circlePreview.frequency}
            </p>
            <h3 className="mt-1 text-xl font-black">{circlePreview.title}</h3>
          </div>
          <span className="rounded-full bg-blue-soft px-3 py-1 text-xs font-extrabold text-link">
            cycle {cycle} of {cycles}
          </span>
        </div>

        <div className="mt-6">
          <div className="flex items-baseline justify-between text-sm font-bold">
            <span>
              {formatNaira(paidCount * amount)}{" "}
              <span className="text-muted-foreground">of {formatNaira(pot)}</span>
            </span>
            <span className="text-muted-foreground">{progress}%</span>
          </div>
          <div className="mt-2 h-4 overflow-hidden rounded-full bg-cloud">
            <div
              className="relative h-full rounded-full bg-green"
              style={{ width: `${progress}%` }}
            >
              <span className="absolute inset-x-2 top-1 h-1 rounded-full bg-white/35" />
            </div>
          </div>
        </div>

        <ul className="mt-6 flex flex-col gap-2.5">
          {members.map((member, i) => (
            <li key={member.name} className="flex items-center gap-3">
              <span
                className={cn(
                  "flex size-9 items-center justify-center rounded-full text-sm font-black text-white",
                  avatarColors[i % avatarColors.length]
                )}
              >
                {initials(member.name)}
              </span>
              <span className="flex-1 text-sm font-bold">
                {member.name}
                {member.name === circlePreview.beneficiary && (
                  <span className="ml-2 rounded-full bg-orange-soft px-2 py-0.5 text-[11px] font-extrabold text-orange-deep dark:text-orange">
                    this cycle&apos;s payout
                  </span>
                )}
              </span>
              {member.paid ? (
                <span className="flex items-center gap-1 text-xs font-extrabold text-green-deep dark:text-green">
                  <HugeiconsIcon icon={Tick02Icon} size={16} strokeWidth={3} />
                  paid
                </span>
              ) : (
                <span className="text-xs font-extrabold text-muted-foreground">pending</span>
              )}
            </li>
          ))}
        </ul>

        <div className="mt-6 flex items-center gap-3 rounded-full bg-cloud p-2 pr-4">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-orange text-white">
            <HugeiconsIcon icon={Store01Icon} size={18} strokeWidth={2.2} />
          </span>
          <p className="text-xs leading-snug font-bold text-muted-foreground">
            payout redeemable only at{" "}
            <span className="text-foreground">{circlePreview.vendor}</span>
          </p>
        </div>
      </div>

      <div className="relative z-10 -mt-5 flex flex-col items-stretch gap-3 px-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="card-raised flex items-center gap-2 self-start rounded-full py-2 pr-4 pl-2 sm:mt-10">
          <span className="flex size-8 items-center justify-center rounded-full bg-primary text-white">
            <HugeiconsIcon icon={Ticket01Icon} size={16} strokeWidth={2.2} />
          </span>
          <span className="text-xs font-extrabold whitespace-nowrap">cycle 1 redeemed by amaka</span>
        </div>
        <ScoreCard />
      </div>
    </div>
  )
}

function ScoreCard() {
  return (
    <div className="card-raised w-full rounded-[1.75rem] p-5 sm:max-w-[16rem]">
      <div className="flex items-baseline justify-between">
        <p className="text-xs font-extrabold tracking-wide text-muted-foreground">sura score</p>
        <p className="text-xs font-bold text-muted-foreground">/ {scorePreview.max}</p>
      </div>
      <p className="mt-1 text-4xl font-black tracking-tight text-primary">{scorePreview.total}</p>
      <ul className="mt-3 flex flex-col gap-2">
        {scorePreview.pillars.map((pillar) => (
          <li key={pillar.label}>
            <div className="flex justify-between text-[11px] font-bold">
              <span>{pillar.label}</span>
              <span className="text-muted-foreground">
                {pillar.points}/{pillar.max}
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-cloud">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${(pillar.points / pillar.max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
