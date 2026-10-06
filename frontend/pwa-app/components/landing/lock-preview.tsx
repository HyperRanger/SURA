import { HugeiconsIcon } from "@hugeicons/react"
import { Calendar03Icon, CheckmarkCircle02Icon, SquareLock01Icon, Tick02Icon } from "@hugeicons/core-free-icons"
import { lockPreview } from "@/config/landing"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { formatNaira, initials } from "@/utils/format"

// an illustrative Lock, drawn like the member home will show it. not live data
export function LockPreview() {
  const { title, frequency, amount, cycle, cycles, vendor, nextPayout, members } = lockPreview
  const paidCount = members.filter((member) => member.paid).length
  const pot = amount * members.length
  const progress = Math.round((paidCount / members.length) * 100)

  return (
    <div aria-hidden="true" className="relative mx-auto w-full max-w-sm select-none md:max-w-md">
      <div className="absolute -top-4 right-2 z-10 flex items-center gap-1.5 rounded-full border-2 border-success/25 bg-success-soft px-3 py-1.5 text-xs font-bold text-success shadow-sm motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-top-2 motion-safe:delay-500 motion-safe:duration-500 motion-safe:fill-mode-backwards">
        <HugeiconsIcon icon={CheckmarkCircle02Icon} size={16} strokeWidth={2.2} />
        Contribution recorded
      </div>

      <div className="card-raised rounded-[2rem] p-5 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-6 motion-safe:duration-700 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-muted-foreground">Rotating · {frequency}</p>
            <p className="mt-0.5 text-xl font-bold">{title}</p>
          </div>
          <Badge className="tabular-nums">
            Cycle {cycle} of {cycles}
          </Badge>
        </div>

        <div className="mt-5 flex items-baseline justify-between">
          <p className="text-3xl font-bold tracking-tight tabular-nums">{formatNaira(amount)}</p>
          <p className="text-xs font-bold text-muted-foreground">each, {frequency.toLowerCase()}</p>
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-xs font-bold">
            <span className="tabular-nums">
              {formatNaira(paidCount * amount)} <span className="text-muted-foreground">of {formatNaira(pot)}</span>
            </span>
            <span className="text-muted-foreground tabular-nums">{progress}%</span>
          </div>
          <div className="mt-2 h-3.5 rounded-full bg-cloud">
            <div className="relative h-full rounded-full bg-gold" style={{ width: `${progress}%` }}>
              <span className="absolute inset-x-2 top-0.5 h-1 rounded-full bg-white/40" />
            </div>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between">
          <ul className="flex -space-x-2">
            {members.map((member) => (
              <li key={member.name} className="relative">
                <span
                  className={cn(
                    "flex size-10 items-center justify-center rounded-full border-[3px] border-card text-sm font-bold",
                    member.paid ? "bg-primary text-primary-foreground" : "bg-cloud text-muted-foreground"
                  )}
                >
                  {initials(member.name)}
                </span>
                {member.paid && (
                  <span className="absolute -right-0.5 -bottom-0.5 flex size-4 items-center justify-center rounded-full border-2 border-card bg-success text-white">
                    <HugeiconsIcon icon={Tick02Icon} size={9} strokeWidth={4} />
                  </span>
                )}
              </li>
            ))}
          </ul>
          <p className="text-xs font-bold text-muted-foreground">
            {paidCount} of {members.length} paid
          </p>
        </div>

        <div className="mt-5 flex items-center gap-3 rounded-2xl bg-cloud p-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-card text-link">
            <HugeiconsIcon icon={Calendar03Icon} size={20} strokeWidth={2} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-muted-foreground">Next payout</p>
            <p className="text-sm font-bold">
              {nextPayout.name} · {nextPayout.date}
            </p>
          </div>
          <p className="text-sm font-bold tabular-nums">{formatNaira(pot)}</p>
        </div>

        <div className="mt-3 flex items-center gap-2 rounded-full bg-primary py-2 pr-4 pl-2 text-primary-foreground">
          <span className="flex size-7 items-center justify-center rounded-full bg-white/15">
            <HugeiconsIcon icon={SquareLock01Icon} size={15} strokeWidth={2.2} />
          </span>
          <p className="text-xs font-bold">
            Payouts locked to <span className="text-gold">{vendor}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
