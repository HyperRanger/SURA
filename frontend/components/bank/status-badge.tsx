import { cn } from "@/lib/utils"
import { humanize } from "@/utils/format"

type StatusTone = "indigo" | "gold" | "neutral" | "danger" | "warning"

const toneClasses: Record<StatusTone, string> = {
  indigo: "border-ring/15 bg-indigo-soft text-link",
  gold: "border-gold/45 bg-gold-soft text-gold-deep",
  neutral: "border-hairline bg-card text-muted-foreground",
  danger: "border-destructive/25 bg-destructive/8 text-destructive",
  warning:
    "border-[#e0a458]/50 bg-[#fdf1e1] text-[#8a4f0b] dark:border-[#e0a458]/35 dark:bg-[#e0a458]/12 dark:text-[#e8b673]",
}

// gold is kept for what has been earned or locked in, as the brand rules ask
const statusTones: Record<string, StatusTone> = {
  active: "indigo",
  pending_members: "neutral",
  scheduled: "neutral",
  pending: "neutral",
  ready: "indigo",
  completed: "gold",
  paid: "gold",
  redeemed: "gold",
  settled: "gold",
  full: "gold",
  eligible: "gold",
  verified: "gold",
  established: "gold",
  building: "indigo",
  entry: "neutral",
  unverified: "neutral",
  locked: "neutral",
  open: "danger",
  missed: "danger",
  failed: "danger",
  high: "danger",
  escalated: "warning",
  medium: "warning",
  partial: "warning",
  reversed: "warning",
  confirmed: "danger",
  dismissed: "neutral",
  cancelled: "neutral",
  expired: "neutral",
  low: "neutral",
  under_review: "warning",
  restricted: "warning",
  suspended: "danger",
  reinstated: "indigo",
  resolved: "neutral",
  revoked: "neutral",
  disabled: "neutral",
  simulated_success: "indigo",
  sandbox: "indigo",
  live: "gold",
  low_risk: "indigo",
  medium_risk: "warning",
  high_risk: "danger",
}

type StatusBadgeProps = {
  status: string | null | undefined
  label?: string
  tone?: StatusTone
  className?: string
}

export function StatusBadge({ status, label, tone, className }: StatusBadgeProps) {
  if (!status) return <span className="text-muted-foreground">—</span>
  return (
    <span
      className={cn(
        "inline-flex w-fit shrink-0 items-center rounded-full border-2 px-2.5 py-0.5 text-xs font-bold whitespace-nowrap",
        toneClasses[tone ?? statusTones[status] ?? "neutral"],
        className
      )}
    >
      {label ?? humanize(status)}
    </span>
  )
}
